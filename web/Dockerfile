# École Platform — Web Frontend Dockerfile
# Reference: Pack E1 — Web Architecture

FROM node:22-alpine AS development

WORKDIR /workspace/web
COPY package*.json ./
RUN npm install
COPY . .

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM node:22-alpine AS build

WORKDIR /workspace/web
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine AS production

COPY --from=build /workspace/web/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
