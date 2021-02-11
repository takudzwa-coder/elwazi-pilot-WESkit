/** Path to which data should be written.*/
params.outputDir

process sayHello
{
    publishDir params.outputDir

	output:
	file 'hello_world.txt' into output_ch

	script:
	"""
	echo 'hello world' > hello_world.txt
	"""
}

/** Check whether parameters are correct (names and values)
 *
 * @param parameters
 * @param allowedParameters
 */
void checkParameters(parameters, List<String> allowedParameters)
{
    Set<String> unknownParameters = parameters.
            keySet().
            grep
            {
              !it.contains('-') // Nextflow creates hyphenated versions of camel-cased parameters.
            }.minus(allowedParameters)
    if (!unknownParameters.empty)
    {
        log.error "There are unrecognized parameters: ${unknownParameters}"
        exit(1)
    }
}

workflow.onComplete
{
    log.info "Success!"
}
