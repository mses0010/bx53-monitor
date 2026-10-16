import asyncio
import httpx
from bs4 import BeautifulSoup

TARGET_URL = "https://www.sen-sen.com.tw/products/beyblade-x-bx-53-all-in-one-set"
DISCORD_WEBHOOK_URL = (
    "https://discord.com/api/webhooks/1560506768067403788/0qRlEHZPJ2pZdN1jBKjpy"
    "IbwahMBr4GBLvjQ1RrhIoHPIBwtIDTn--BMwQBslFjkCHCK"
)


async def send_discord_notification(message):
  async with httpx.AsyncClient() as client:
    try:
      await client.post(
          DISCORD_WEBHOOK_URL, json={"content": message}, timeout=10
      )
      print("Discord 通知發送成功！")
    except Exception as e:
      print(f"發送失敗: {e}")


async def check_once(client):
  try:
    response = await client.get(
        TARGET_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10, follow_redirects=True
    )
    if response.status_code != 200:
      print(f"網頁連線異常，狀態碼: {response.status_code}")
      return False

    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text()

    add_to_cart_btn = soup.find(
        string=lambda t: t and any(keyword in t for keyword in ["加入購物車", "立即購買"])
    )
    sold_out_keywords = ["售完", "缺貨", "SOLD OUT", "已售罄"]
    is_sold_out = any(keyword in page_text for keyword in sold_out_keywords)

    if add_to_cart_btn and not is_sold_out:
      return True
    return False
  except Exception as e:
    print(f"檢查發生錯誤: {e}")
    return False


async def main():
  async with httpx.AsyncClient() as client:
    # 第一次檢查（第 0 秒）
    print("正在進行第一次檢查...")
    if await check_once(client):
      print(">>> 發現有貨！")
      await send_discord_notification(
          "🚨 **@everyone ［BX-53 補貨啦！］** 🚨\nGitHub 雲端偵測到商品已可購買，請立刻手刀搶購！\n🔗 快速連結：" + TARGET_URL
      )
      return
    else:
      print("目前無庫存。")

    # 等待 30 秒
    print("等待 30 秒後進行第二次檢查...")
    await asyncio.sleep(30)

    # 第二次檢查（第 30 秒）
    print("正在進行第二次檢查...")
    if await check_once(client):
      print(">>> 發現有貨！")
      await send_discord_notification(
          "🚨 **@everyone ［BX-53 補貨啦！］** 🚨\nGitHub 雲端偵測到商品已可購買，請立刻手刀搶購！\n🔗 快速連結：" + TARGET_URL
      )
    else:
      print("目前無庫存。")


if __name__ == "__main__":
  asyncio.run(main())