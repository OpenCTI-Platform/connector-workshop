# OpenCTI Lab

OpenCTI lab ready to run in Docker Compose. This is a minimal stack for running the lab exercises, it is not intended for production use.

This instance is for local purposes only, it is not reachable from the internet.

## Lab prerequisites

Having docker installed and running is a prerequisite for the lab. If you are using WSL, make sure to install Docker natively on the WSL side and not via Docker Desktop integration. All commands below assume a WSL/Ubuntu shell.

```bash
# check docker is installed and running
docker --version
cp .env.sample .env # then edit the required variables
docker compose up -d
docker 
```

The `minio` service runs [RustFS](https://rustfs.com), an open source S3-compatible object storage, under its former service name and `MINIO_ROOT_*` variables. It keeps its files in the `rustfsdata` volume.

### Upgrading a lab that ran Silo

If `docker volume ls` shows `xtm_s3data` (`<COMPOSE_PROJECT_NAME>_s3data`) from a previous lab, reset the lab before using it: the storage starts empty while OpenCTI and XTM One keep their data. This erases all lab data (OpenCTI, XTM One, RabbitMQ, keys):

```bash
docker compose down -v
docker compose up -d
```

`down -v` does not remove the former `xtm_s3data` volume. Remove it with `docker volume rm xtm_s3data`, unless an OpenCTI stack from [OpenCTI-Platform/docker](https://github.com/OpenCTI-Platform/docker) runs under the same project name: that stack keeps its storage in this volume.

## Check the platform is healthy

Check connection to the platform with the provided Python script:

```bash
pip install pycti
python check-connection.py
```

Result

![Check connection result](../docs/media/check-connection-success.png)

## Known issues

Running the connector locally will give you the following error when you connect to the platform because you'll need all the context (RabbitMQ, worker) too.

```
message": "AMQP connection workflow failed: AMQPConnectionWorkflowFailed: 1 exceptions in all; last exception - AMQPConnectorSocketConnectError: TimeoutError(\"TCP connection attempt timed out: 'rabbitmq'/(<AddressFamily.AF_INET: 2>, <SocketKind.SOCK_STREAM: 1>, 6, '', ('172.23.0.5', 5672))\"); first exception - None."}
```

### Solution on Windows OS: Add RabbitMQ service to allow the context

- Go to C:/Windows/System32/drivers/etc
- Open the file `hosts` with a text editor (e.g., Notepad) with admin rights

![Win hosts file](../docs/media/win-hosts.png)

- Add the following line to the end of the file:
  
  ```txt
  127.0.0.1 rabbitmq
  ```

![Win hosts file updated](../docs/media/win-hosts-updated.png)
