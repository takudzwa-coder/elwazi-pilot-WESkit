<!--
SPDX-FileCopyrightText: 2023 The WESkit Contributors

SPDX-License-Identifier: MIT
-->

# Contributing

**Thank you for submitting your contributions to this project.**

All types of contributions are encouraged and valued, including feature requests, bug reports, documentation improvements.

Please make sure to read the relevant section in this document before making your contribution.

> If you like the project, please support the project and show your appreciation by
> - Sharing it on social media
> - Referring this project in your own project's readme
> - Mentioning the project at local meetups and telling your friends/colleagues

## Table of Contents

- [Contributors License Agreement](#contributor-license-agreement)
- [Signing off your work](#sign-off-your-work)
- [I Have a Question](#i-have-a-question)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Coding Conventions & Co.](#coding-conventions-and-co)

## Contributor License Agreement
<!-- The text of this CLA is based on fragments of CLA texts found in various projects. -->

This contributors license agreement (CLA) has the purpose to add documentation requirements and terms related to the provenance of contributions that are not covered by the license of the project.

If you find that the CLA contradicts the license in any way, then the text of the license has priority over anything written in this CLA.

By signing this CLA, you agree that the following terms apply to your contributions.

> You sign the CLA by adding to every commit of your contributions a "Signed-off-by:" tag in the commit message.
> This is easily done by adding the `-s` option to the `git commit` command. See section [Sign off Your Work](#sign-off-your-work).

### License

Your contributions will be published under [MIT License](https://opensource.org/licenses/MIT).

### Moral Rights.

To the fullest extent permitted under applicable law, you hereby waive, and agree not to
assert, all of your [“moral rights”](https://en.wikipedia.org/wiki/Moral_rights) in or relating to your contributions for the benefit of the project.

> [Moral rights](https://en.wikipedia.org/wiki/Moral_rights) refer to the right of attribution, the right to have the work published anonymously or pseudonymously, and the right of the integrity of the work.
>

> We cannot grant you anonymity or pseudonymity, because WESkit may be used in a regulated context.
>

> We think that the right of attribution and integrity of the work is already waived by accepting MIT as new license.
>

> These explanations are not limiting the meaning of "all of your moral rights".

### Third Party Content

You agree to include with the submission of your contribution full details respecting Third Party Content.

Third Party Content is any part of your contribution that is based on any source code, object code, bug fixes, configuration changes, tools,
specifications, documentation, data, materials, feedback, information or other works of authorship that were not
_authored_ by you or if there are third party intellectual property or proprietary
rights associated with your contribution (“Third Party Rights”).

You also agree to document all parts of your contribution that are Third Party Content or are associated with Third Party Rights as follows

  * Identify all aspects and modifications of your contribution that contain Third Party Content or are associated with Third Party Rights

  * Reference the owner/author of the Third Party Content and Third Party Rights, where you obtained the Third Party Content.
  * List any applicable third party license terms or restrictions respecting the Third Party Content and Third Party Rights.

### Representations

You represent that,
other than the Third Party Content and Third Party Rights identified by you in accordance with this agreement,

you are the sole author of your contributions and are legally entitled to grant terms and conditions of this CLA for your contributions.

If your contributions were created in the course of your employment with your past or present employer(s), you represent

that such employer(s) has authorized you to make your contributions on behalf of such employer(s) or
that such employer(s) has waived all of their right, title or interest in or to your contributions.

> Note that this can be a particular problem for code snippets from websites such as [StackOverflow](https://stackoverflow.com/legal/terms-of-service/public).

### Disclaimer

To the fullest extent permitted under applicable law, your contributions are provided on an "as is"
basis, without any warranties or conditions, expressed or implied, including, without limitation, any implied
warranties or conditions of non-infringement, merchantability or fitness for a particular purpose. You are not
required to provide support for your Contributions, except to the extent you desire to provide support.

### No Obligation.

You acknowledge that the maintainers of this project are under no obligation to use or incorporate your contributions
into the project. The decision to use or incorporate your contributions into the project will be made at the
sole discretion of the maintainers or their authorized delegates.

## Sign off Your Work

Contributors must sign off that they adhere to the terms and conditions of the CLA.

This is done on a per commit base, and can easily be done by adding the `-s` option to `git commit`:

See `git help commit`:

```text
-s, --signoff
    Add a Signed-off-by trailer by the committer at the end of the

    commit log message. The meaning of a signoff depends on the project
    to which you're committing.
```

Thus, committing is as easy as

```bash
git commit -s
```

Your commit message will then be extended by a "Signed-of-by:" tag similar to the following:

```text
This is my commit message

Signed-off-by: Random J Developer <random@developer.example.org>
```

> Note: GitLab will ensure that all commits are signed-off.

## I Have a Question

There are some resources that may already answer many of your questions, namely

* the [documentation](https://gitlab.com/one-touch-pipeline/weskit/documentation)
* existing [issues](https://gitlab.com/one-touch-pipeline/weskit/api/issues)

If these resources do not answer your questions, you can contact us by opening a new [issue](https://gitlab.com/one-touch-pipeline/weskit/api/issues/new). Please follow the guidelines in the issue templates for details.
We will then take care of the issue as soon as possible.

Feel free to ask questions, because they help us to understand the gaps in our documentation or hint at new use cases and requirements. This will help us to improve WESkit's usability for the use cases we want to address, and help us to better understand the domains in which WESkit is applied.

### Reporting Bugs

We use Gitlab issues to track bugs and errors. If you run into an issue with the project

- open an [issue](https://gitlab.com/one-touch-pipeline/weskit/api/issues/new) using the bug template ("Description" drop-down list).
- provide as much context as possible within each subsection of the template.

> The better your bug report is, the better we will be able to fix the bug!

Once the bug report is filed

- the project team will label the issue accordingly.
- a team member will try to reproduce the issue with your provided steps and otherwise come back to you.

> WARNING: For submitting security-related bug you should not post bug report as GitLab issue. In this case, please report the bug at <weskit@dkfz-heidelberg.de>.

### Suggesting Features

Like bugs, we track feature requests in Gitlab issues, and have a dedicated feature issue template for this. The template should help you to write a good request, that helps us to understand your use case.

## Branching Scheme

We are using [Github-Flow](https://docs.github.com/en/get-started/quickstart/github-flow) scheme, which is well explained for instance [here](https://www.alexhyett.com/git-flow-github-flow/).

Shortly, we have a "master" branch on which we always keep only stable code. The master branch should always pass all tests. The master branch is also protected. Only from the master branch we release by tagging commits.

We then branch off "feature" branches with descriptive names. Feature branches may not always compile, but the Gitlab-CI ensures that they do so after merging with the master branch.

## Coding Conventions and Co.

We use the Gitlab-CI to enforce certain coding conventions in our code and improve overall code quality.

You can enforce these conventions in your local repository copies simply by symlink the git-hooks:

```bash
cd $projectDir/.git/hooks
ln -s ../../git/hooks/* .
```

If you need to turn of the commit or push checks during your work on a branch, you can do this on a per commit base with

```bash
NO_COMMIT_CHECKS=true git commit -s
NO_PUSH_CHECKS=true git push
```

### Testing

Unit and integration tests are implemented with [pytest](https://docs.pytest.org). New code should always have a test coverage above 80%. The more the better, but of course only as is reasonable. We don't require tests for simple getters, for instance.

### Code Style

Code style is enforced by [flake8](https://flake8.pycqa.org/).

### Python Type Checking

One of the greatest shortcomings of Python for the development of more complex projects is its lack of built-in static type checks. Fortunately, there are static type checkers that, when applied, identify a lot of bugs that otherwise could break production deployments.

We use [mypy](https://mypy.readthedocs.io/en/stable/) for static type checking.

### Automated Security Checks

Some security bugs are discovered by [bandit](https://bandit.readthedocs.io/). Contributions to improve our security monitoring and the code security are very welcome.

### License Management

Finally, we require that all files have an [SPDX](https://spdx.dev/) license header. We use [reuse](https://spdx.dev/) to check this in the CI. Reuse is also a good too for managing the headers.
