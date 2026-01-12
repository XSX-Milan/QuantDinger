# TELEGRAM通知配置

## 1.创建telegram机器人并且获取token
<img src="./screenshots/notification_telegram_token.png" alt="QuantDinger Dashboard" width="100%" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">

## 2.1 在策略中配置UserID
<img src="./screenshots/notification_telegram_userid.png" alt="QuantDinger Dashboard" width="100%" style="border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">

## 2.2 UserID的获取
```aiignore
https://api.telegram.org/bot【你的哪个token】/getUpdates
```
UserID从这个链接获取，把你的token填进去，token格式是【123:abc】
![notification_telegram_userid_get.png](screenshots/notification_telegram_userid_get.png)