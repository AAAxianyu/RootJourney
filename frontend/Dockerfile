# 直接使用HTML文件，不需要构建
FROM nginx:alpine

# 复制HTML文件到nginx目录
COPY public/index.html /usr/share/nginx/html/index.html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

