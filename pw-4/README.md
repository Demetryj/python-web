# A simple HTTP server with sockets.

## Caution regarding data storage in Docker

This container is started with the `<volume_name>` volume:
`-v <volume_name>:/app/storage`

This means all data from `/app/storage` (including `data.json`) is stored in a Docker volume on the host, not in the project folder. Because of this, the local file `./storage/data.json` may not change even when the app successfully writes data inside the container.

Why this is useful:

1. Data is not lost when the container is restarted or recreated.
2. Data is separated from the image and application code.
3. The same volume can be attached to newer container versions.

If you want to store data directly in the local project folder, use a bind mount:
`-v ./storage:/app/storage`

### Commands for working with Docker

**Image creation**

```bush
docker build -t <image-name> <dir>
```

**Create volume**

```bush
docker volume create <volume_name>
```

**Creating and running a container**

```bush
docker run -d -p 3000:3000 --name <container-name> -v <volume_name>:/app/storage <image-name>
```

**View data saved from an application form**

```bush
docker exec -it <container-name> sh -c "ls -la /app/storage && cat /app/storage/data.json"
```
