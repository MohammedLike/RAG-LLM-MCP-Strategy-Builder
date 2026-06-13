FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

RUN chmod +x docker-entrypoint.sh

EXPOSE 5075

ENTRYPOINT ["./docker-entrypoint.sh"]
