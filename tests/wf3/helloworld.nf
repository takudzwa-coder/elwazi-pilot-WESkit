/*
 * Copyright (c) 2023. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
 *
 * Distributed under the MIT License. Full text at
 *
 *     https://gitlab.com/one-touch-pipeline/weskit/api/-/blob/master/LICENSE
 *
 * Authors: The WESkit Team
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
