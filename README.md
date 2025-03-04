# BEHAVE

Converting (any) behavioural data into BIDS

## Docker usage

```bash
docker build -t behave .
```

Run with your files

```bash
docker run -v /path/to/data:/data -v /path/to/resources:/resources -it behave
```

### How It Works
Local Files:

Your local files (e.g., Excel files in /data and /resources) reside on your host machine (your computer).
Docker Container:

The Docker container is an isolated environment where your application runs. By default, it doesn't include your local files.
Volume Mounting (-v):

When you run the Docker container with the -v option, you "mount" your local directories into the container. This means:
The container can access the files in /data and /resources as if they were inside the container.
But the files are still physically stored on your host machine, not in the container.

![Drag Racing](LOGO.png)
