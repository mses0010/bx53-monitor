import asyncio
from datetime import datetime, timedelta, timezone
import traceback
import httpx

API_URL = (
    "https://www.sen-sen.com.tw/products/beyblade-x-bx-53-all-in-one-set.json"
)
DISCORD_WEBHOOK_URL = (
    "https://discord.com/api/webhooks/1560506768067403788/0qRlEHZPJ2pZdN1jBKjpy"
    "IbwahMBr4GBLvjQ1RrhIoHPIBwtIDTn--BMwQBslFjkCHCK"
)

# 設定台灣時區 (UTC+8)
TAIWAN_TZ = timezone(timedelta(hours=8))


async def send_discord_notification(message):
  async with httpx.AsyncClient(timeout=15.0) as client:
    try:
      await client.post(DISCORD_WEBHOOK_URL, json={"content": message})
      print("Discord 通知發送成功！")
    except Exception as e:
      print(f"發送失敗: {e}")


async def check_once(client):
  response = await client.get(API_URL)
  if response.status_code != 200:
    print(f"API 回應異常，狀態碼: {response.status_code}")
    return False

  data = response.json()
  product_info = data.get("product", data)
  price = product_info.get("price", 0)
  variants = product_info.get("variants", [])

  is_in_stock = False
  for variant in variants:
    inventory_quantity = variant.get("inventory_quantity", 0)
    available = variant.get("available", True)
    if available and inventory_quantity > 0:
      is_in_stock = True
      break

  if is_in_stock or (price > 0 and product_info.get("available", False)):
    title = product_info.get("title", "BX-53 全方位套裝")
    await send_discord_notification(
        f"🚨 **@everyone ［BX-53 補貨/上架啦！］** 🚨\n- 商品：{title}\n- 價格："
        f" {price}\n- 🔗 快速連結：https://www.sen-sen.com.tw/products/"
        "beyblade-x-bx-53-all-in-one-set"
    )
    return True

  return False


async def main():
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
      ),
      "Accept": "application/json",
  }

  async with httpx.AsyncClient(headers=headers, timeout=20.0) as client:
    try:
      # ⚡ 升級版高密度內循環：每 15 秒檢查一次，連續跑 112 次（總計約 28 分鐘）
      # 這樣可以完美無縫銜接大約 30 分鐘一次的 GitHub 觸發間隔，空窗期小於 30 秒！
      total_checks = 112
      sleep_seconds = 15

      for i in range(total_checks):
        current_time = datetime.now(TAIWAN_TZ)
        print(
            f"--- 台灣時間 {current_time.strftime('%H:%M:%S')} 執行第"
            f" {i+1}/{total_checks} 次檢查 ---"
        )

        found = await check_once(client)
        if found:
          print(">>> 發現有貨，已發送 Discord 通知！")
          return

        # 最後一次檢查完不需要再 sleep
        if i < total_checks - 1:
          await asyncio.sleep(sleep_seconds)

      print("本輪高密度監控結束，等待下次觸發。")

    except Exception as e:
      error_msg = traceback.format_exc()
      print(f"檢查發生詳細錯誤:\n{error_msg}")


if __name__ == "__main__":
  asyncio.run(main())