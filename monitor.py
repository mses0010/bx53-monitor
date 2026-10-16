import asyncio
from datetime import datetime
import os
import traceback
import httpx

# 這是該商品在後台的實際 JSON API 接口
API_URL = (
    "https://www.sen-sen.com.tw/products/beyblade-x-bx-53-all-in-one-set.json"
)
DISCORD_WEBHOOK_URL = (
    "https://discord.com/api/webhooks/1560506768067403788/0qRlEHZPJ2pZdN1jBKjpy"
    "IbwahMBr4GBLvjQ1RrhIoHPIBwtIDTn--BMwQBslFjkCHCK"
)

STATE_FILE = "last_report_hour.txt"


async def send_discord_notification(message):
  async with httpx.AsyncClient(timeout=15.0) as client:
    try:
      await client.post(DISCORD_WEBHOOK_URL, json={"content": message})
      print("Discord 通知發送成功！")
    except Exception as e:
      print(f"發送失敗: {e}")


async def main():
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
      ),
      "Accept": "application/json",
  }

  current_time = datetime.now()
  current_hour = current_time.hour
  current_minute = current_time.minute

  async with httpx.AsyncClient(headers=headers, timeout=20.0) as client:
    try:
      print(f"正在請求 API: {API_URL}")
      response = await client.get(API_URL)
      print(f"API 狀態碼: {response.status_code}")

      if response.status_code != 200:
        print(f"API 回應異常，狀態碼: {response.status_code}")
        return

      # 解析後台 JSON 數據
      data = response.json()

      # 根據 Cybassets 平台結構解析商品與庫存
      # 通常可以檢查 variants 裡的庫存或 price 是否大於 0
      product_info = data.get("product", data)
      title = product_info.get("title", "BX-53 全方位套裝")
      price = product_info.get("price", 0)
      variants = product_info.get("variants", [])

      # 檢查是否有任何一個規格有庫存或可購買
      is_in_stock = False
      for variant in variants:
        inventory_quantity = variant.get("inventory_quantity", 0)
        available = variant.get("available", True)
        if available and inventory_quantity > 0:
          is_in_stock = True
          break

      # 如果價格大於 0 且庫存大於 0，或者標題/狀態顯示可買
      if is_in_stock or (price > 0 and product_info.get("available", False)):
        print(">>> 發現有貨或已正式上架！")
        await send_discord_notification(
            f"🚨 **@everyone ［BX-53 補貨/上架啦！］** 🚨\n- 商品：{title}\n- 價格："
            f" {price}\n- 🔗 快速連結：https://www.sen-sen.com.tw/products/"
            "beyblade-x-bx-53-all-in-one-set"
        )
        return

      # 每小時心跳回報邏輯
      should_report_hourly = current_minute < 5
      is_reported_this_hour = False
      if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
          last_hour = f.read().strip()
          if last_hour == str(current_hour):
            is_reported_this_hour = True

      if should_report_hourly and not is_reported_this_hour:
        with open(STATE_FILE, "w") as f:
          f.write(str(current_hour))

        hourly_msg = (
            f"🕒 **[BX-53 雲端 API 監控心跳報告]**\n- 狀態：🟢 運行中（目前無庫存/未標價）\n-"
            f" 檢查時間：`{current_time.strftime('%Y-%m-%d %H:%M')}`"
        )
        await send_discord_notification(hourly_msg)
        print("已發送每小時狀態回報！")
      else:
        print("目前無庫存，安靜監控中...")

    except Exception as e:
      error_msg = traceback.format_exc()
      print(f"檢查發生詳細錯誤:\n{error_msg}")


if __name__ == "__main__":
  asyncio.run(main())