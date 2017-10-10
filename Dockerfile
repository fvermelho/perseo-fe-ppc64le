FROM ppc64le/node:4

WORKDIR /opt/perseo-fe
ENV PERSEO_MONGO_HOST=mongodb
ENV PERSEO_CORE_URL=http://corehost:8080
EXPOSE 9090

COPY package.json /opt/perseo-fe/package.json
COPY npm-shrinkwrap.json /opt/perseo-fe/npm-shrinkwrap.json
RUN npm install --production

COPY . /opt/perseo-fe/
CMD bin/perseo
