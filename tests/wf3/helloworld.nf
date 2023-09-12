/*
 * SPDX-FileCopyrightText: 2023 The WESkit Contributors
 *
 * SPDX-License-Identifier: MIT
 */

params.text = "Ups! No 'hello'!"

process sayHello {
    publishDir "./", mode: "rellink"

	output:
	file 'hello_world.txt'

	script:
	"""
	echo '$params.text' > hello_world.txt
	"""
}

workflow {
	sayHello()
}


workflow.onComplete {
    log.info "Success!"
}
