#!/usr/bin/env bash

set -eu -o pipefail
shopt -s inherit_errexit

trap 'echo "Failed in line $LINENO"' ERR
trap 'popd > /dev/null' EXIT

expect_fail() {
  true
}

wrap="$(readlink -f "wrap")"

testDir=$(mktemp -d wrap_test-XXXX)
echo "Test data go to $testDir" >> /dev/stderr
pushd "$testDir" > /dev/null

{
  test=eval_fail_stdout_stderr
  $wrap -l "$test"  -a -- "echo hallo; echo du > /dev/stderr; exit 1" \
    > "$test.json" \
    || expect_fail
  [ "$(wc -l "$test.json" | cut -f 1 -d ' ')" -eq 11 ]
  [ "$(cat "$test.json" | jq .exit_code )" -eq 1 ]
  [ "$(cat "$test/exit_code")" -eq 1 ]
  [ "$(cat "$test/stdout")" == "hallo" ]
  [ "$(cat "$test/stderr")" == "du" ]
  [ "$(cat "$test.json" | jq -r .stdinFile )" == "/dev/null" ]
  [ "$(cat "$test.json" | jq -r .stdoutFile )" == "$test/stdout" ]
  [ "$(cat "$test.json" | jq -r .stderrFile )" == "$test/stderr" ]
  [ "$(cat "$test.json" | jq -r .exitFile )" == "$test/exit_code" ]
  [ "$(cat "$test.json" | jq -r .pidFile )" == "$test/pid" ]
  [ "$(cat "$test.json" | jq -r .envFile )" == "/dev/null" ]
}

{
  test="eval_success_stdout_stderr"
  $wrap -l "$test"  -a -- "echo hallo; echo du > /dev/stderr; exit 0" \
    > "$test.json"
  [ "$(cat "$test.json" | jq .exit_code )" -eq 0 ]
  [ "$(cat "$test/exit_code")" -eq 0 ]
}

{
  test="fail"
  $wrap -l "$test"  -a -- false \
    > "$test.json" \
    || expect_fail
  [ "$(wc -l "$test.json" | cut -f 1 -d ' ')" -eq 11 ]
  [ "$(cat "$test.json" | jq .exit_code )" -eq 1 ]
  [ "$(cat "$test/exit_code")" -eq 1 ]
  [ "$(cat "$test/stdout")" == "" ]
  [ "$(cat "$test/stderr")" == "" ]
}

# To test the outputs and failure without `eval` we use an exported function.
run_with_output() {
  echo "out" >> /dev/stdout
  echo "err" >> /dev/stderr
  exit "$1"
}
export -f run_with_output

{
  test="fail_stdout_stderr"
  $wrap -l "$test" -o "./$test.stdout" -e "$PWD/$test.stderr" -p "$test.pid" -x "$test.exit_code" \
    -- run_with_output 11 \
    > "$test.json" \
    || expect_fail
  [ "$(wc -l "$test.json" | cut -f 1 -d ' ')" -eq 11 ]
  [ "$(cat "$test.json" | jq .exit_code )" -eq 11 ]
  [ "$(cat "$test/$test.exit_code")" -eq 11 ]
  [ -f "$test/$test.pid" ]
  [ "$(cat "$test.stdout")" == "out" ]
  [ "$(cat "$test.stderr")" == "err" ]
  [ "$(cat "$test.json" | jq -r .stdoutFile )" == "./$test.stdout" ]
  [ "$(cat "$test.json" | jq -r .stderrFile )" == "$PWD/$test.stderr" ]
  [ "$(cat "$test.json" | jq -r .exitFile )" == "$test/$test.exit_code" ]
  [ "$(cat "$test.json" | jq -r .pidFile )" == "$test/$test.pid" ]
}

{
  test="success_stdout_stderr"
  $wrap -l "$test" -- run_with_output 0 \
    > "$test.json"
  [ "$(cat "$test.json" | jq .exit_code )" -eq 0 ]
  [ "$(cat "$test/exit_code")" -eq 0 ]
  [ "$(cat "$test/stdout")" == "out" ]
  [ "$(cat "$test/stderr")" == "err" ]
}

run_with_input() {
  cat - > /dev/stdout
}
export -f run_with_input

{
  test="success_stdin_stdout"
  # To test the stdin feature without eval we can use again a function.
  echo "hello" > "$test.stdin"
  $wrap -l "$test" -i "$test.stdin" -- run_with_input \
    > "$test.json"
  [ "$(cat "$test.json" | jq .exit_code )" -eq 0 ]
  [ "$(cat "$test.json" | jq -r .stdinFile )" == "$test.stdin" ]
  [ "$(cat "$test/exit_code")" -eq 0 ]
  [ "$(cat "$test/stdout")" == "hello" ]
  [ "$(cat "$test/stderr")" == "" ]
}



echo_envVal() {
  set -u
  # shellcheck disable=SC2154
  echo "$actualEnvVal"
}
export -f echo_envVal

{
  test="environment_file"
  envFile="$(mktemp "XXXX-test-environment.txt")"
  echo "export actualEnvVal='from environment file'" >> "$envFile"
  $wrap -l "$test" -n "$envFile" -- echo_envVal \
      > "$test.json"
  [ "$(cat "$test/exit_code")" -eq 0 ]
  [ "$(cat "$test.json" | jq -r .envFile)" == "$envFile" ]
  [ "$(cat "$test/stdout")" == "from environment file" ]
}

echo "Success"