# BioPulse · SSL 证书

## 证书放置位置

将证书文件放入此目录或引用系统路径 `/etc/letsencrypt/live/biopulse.example.com/`。

Nginx 配置引用（`deploy/nginx/biopulse.conf`）：

```nginx
ssl_certificate /etc/letsencrypt/live/biopulse.example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/biopulse.example.com/privkey.pem;
ssl_trusted_certificate /etc/letsencrypt/live/biopulse.example.com/chain.pem;
```

## 生成证书

### Let's Encrypt（推荐）

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d biopulse.example.com
```

### 自签名（开发环境）

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/biopulse.key \
  -out ssl/biopulse.crt \
  -subj "/CN=biopulse.example.com"
```

## 自动续期

certbot 自动续期，每天检查两次，到期前 30 天续期。

```bash
sudo certbot renew --dry-run
```

详见 `deploy/nginx/ssl-config.md`。
