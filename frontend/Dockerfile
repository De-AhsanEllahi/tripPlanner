FROM node:22-alpine

WORKDIR /app

# Enable corepack
RUN corepack enable

# Use stable pnpm
RUN corepack prepare pnpm@9.12.0 --activate

COPY package.json pnpm-lock.yaml ./

RUN pnpm install

COPY . .

EXPOSE 5173

CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "5173"]