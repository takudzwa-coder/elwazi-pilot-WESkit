/*
 * Copyright (c) 2021. Berlin Institute of Health (BIH) and Deutsches Krebsforschungszentrum (DKFZ).
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
	file 'hello_world.txt' into output_ch

	script:
	"""
	echo '$params.text' > hello_world.txt
	"""
}

workflow.onComplete {
    log.info "Success!"
}
