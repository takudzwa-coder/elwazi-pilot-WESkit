process sayHello {
    publishDir './'

	output:
	file 'hello_world.txt' into output_ch

	script:
	"""
	echo 'hello world' > hello_world.txt
	"""
}

