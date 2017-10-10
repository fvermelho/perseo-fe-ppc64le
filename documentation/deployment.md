<a name="deployment"></a>
## Deployment

### Dependencies

The CEP is a standard Node.js app and doesn't require more dependencies than the Node.js interpreter (0.10) and the NPM package utility.

A mongoDB 3.2 database should be working and accesible before perseo can be started

### Build your own Docker image
There is also the possibility to build your own local Docker image of the Perseo-FE component.

To do it, follow the next steps once you have installed Docker in your machine:

1. Navigate to the path where the component repository was cloned.
2. Launch a Docker build
    * Using the default NodeJS version of the operating system used defined in FROM keyword of Dockerfile:
    ```bash
    sudo docker build -f Dockerfile -t perseo-fe .
    ```
    * Using an alternative NodeJS version:
    ```bash
    sudo docker build --build-arg NODEJS_VERSION=0.10.46 -f Dockerfile -t perseo-fe .
    ```

### Installation using Docker

The last development version is uploaded as a Docker image to Docker Hub for every PR merged into the `master` branch.
Perseo FE needs some components to be present event to be started. Those components can be configured using:

* Environment variables, as in the following example:
```
docker run -e "PERSEO_MONGO_HOST=127.0.0.1" -e "PERSEO_CORE_URL=http://127.0.0.1:8080" telefonicaiot/perseo-fe
```

* Or links to other docker images running in the same docker host, as in the following example:
```
docker run --link corehost:corehost --link mongodb:mongodb fiwareiotplatform/perseocore
```

In order to link other Docker images to the Perso FE image, take into account that it has two requirements:
`
* A **Mongo DB** instance: the image looks for a Mongo DB instance in the `mongodb` alias (port `27017`) when it starts.
* A **Perseo Core** instance: the instance expects a instance of Perseo Core running in the alias `corehost`, port 8080.

For the full perseo stack to work, both instances should be linked to their appropriate alias.

### Running together with Perseo Core and Orion Context Broker

Below it is shown how to run together [Perseo Core](http://github.com/telefonicaid/perseo-core) and Perseo Front-End. 

Assuming there is a Mongo DB container already running (named `mongo`) and an [Orion Context Broker](http://github.com/telefonicaid/fiware.orion) one (named `orion`). 

First a container running Perseo Core has to be instantiated and run (hostname of this container will be `perseocore` and will be listening on port `8080`):

```
docker run -d --name perseo_core -h perseocore -p 8080:8080 telefonicaiot/perseo-core:master -perseo_fe_url <perseo_fe_addr>:9090
```

where <perseo_fe_addr> must be the host name or IP address of the *machine hosting the Perseo FE Container*. Please note that it is a good idea to
expose port `8080` to the host so that it can be verified that Perseo Core is up and running. 

Then a container running Perseo Front-End has to be instantiated and run: 

```
docker run -d -p 9090:9090 --name perseo_fe -h perseo --link perseo_core --link mongo --link orion -e "PERSEO_MONGO_HOST=mongo" -e "PERSEO_CORE_URL=http://perseocore:8080" -e "PERSEO_LOG_LEVEL=debug" -e "PERSEO_ORION_URL=http://orion:1026/v1/updateContext" telefonicaiot/perseo-fe:master
```

Please note that we use the name `perseocore` to refer to the container where Perseo Core is running (previously linked). Similarly we use use the names `orion` and 
`mongo` to refer to the containers where Mongo DB and Orion Context Broker are running. 

To check that Perseo Front-End has been instantiated properly you can run:

```
curl http://localhost:9090/version
```

or

```
curl  http://localhost:9090/rules
```

To check that Perseo Core has been instantiated properly you can run:

```
curl http://localhost:8080/perseo-core/version
```

You can get access to the logs generated by both components:

```
docker logs perseo_fe
```

```
docker exec perseo_core tail -f /var/log/perseo/perseo-core.log
```


### Installation from RPM

This project provides the specs to create the RPM Package for the project, that may (in the future) be installed in a
package repository.

To generate the RPM, checkout the project to a machine with the RPM Build Tools installed, and, from the `rpm/` folder,
execute the following command:

```
./create-rpm.sh 0.1 1
```

The create-rpm.sh script uses the following parameters:

* CEP version (0.1 in the example above), which is the base version of the software
* CEP release (1 in the example above), tipically set with the commit number corresponding to the RPM.

This command will generate some folders, including one called RPMS, holding the RPM created for every architecture
(x86_64 is currently generated).

In order to install the generated RPM from the local file, use the following command:

```
yum --nogpgcheck localinstall  perseo-cep-0.1-1.x86_64.rpm
```

It should automatically download all the dependencies provided they are available (Node.js and NPM may require the
EPEL repositories to be added).

The RPM package can also be deployed in a artifact repository and the installed using:

```
yum install perseo-cep
```

NOTE: Perseo CEP Core is not installed as part of the dependencies in the RPM, so the URL of an existing Perseo Core
must be provided and configured for Perseo to work properly.

#### Activate service
The perseo service is disabled once its installed. In order to enable it, use the following command:
```
service perseo start
```

### Installation from Sources
#### Installation

Just checkout this directory and install the Node.js dependencies using:

```
npm install --production
```

The CEP should be then ready to be configured and used.

#### Undeployment
In order to undeploy the proxy just kill the process and remove the directory.


### Log Rotation
Independently of how the service is installed, the log files will need an external rotation (e.g.: the logrotate command) to avoid disk full problems.

Logrotate is installed as RPM dependency along with perseo. The system is configured to rotate every day and whenever the log file size is greater than 100MB (checked very 30 minutes by default):
* For daily rotation: /etc/logrotate.d/logrotate-perseo-daily: which enables daily log rotation
* For size-based rotation:
	* /etc/sysconfig/logrotate-perseo-size: in addition to the previous rotation, this file ensures log rotation if the log file grows beyond a given threshold (100 MB by default)
	* /etc/cron.d/cron-logrotate-perseo-size: which ensures the execution of etc/sysconfig/logrotate-perseo-size at a regular frecuency (default is 30 minutes)