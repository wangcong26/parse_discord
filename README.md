How to download historical chat?
https://www.youtube.com/watch?v=eoM2-s3HxPc


Install discord.py

1. Open Anaconda prompt command line

2. Navigate to the location of project you want to install discord.

3. Activate conda env if interpreter is using a conda env

	```shell
	# activate the env
	conda activate env_py39
	
	# install discord
	pip install discord.py
	```

4. Test installation

   ```python
   import discord
   
   print("discord.py version:", discord.__version__)
   ```


   