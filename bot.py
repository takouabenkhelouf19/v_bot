import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from PIL import Image
from dotenv import load_dotenv

load_dotenv()  # تحميل المتغيرات البيئية من Render

TOKEN = os.getenv("TOKEN")  # قراءة التوكن من البيئة

bot = Bot(token=TOKEN)
dp = Dispatcher()


def create_final_image(template_path, user_photo_path, output_path):

    template = Image.open(template_path).convert("RGBA")
    user_photo = Image.open(user_photo_path).convert("RGBA")

    # --- 1) نخلو خلفية الصورة بنفس قياسات التومبلايت --- #
    template_w, template_h = template.size

    # نقيس نسب الصورة باش نكورها للعرض كامل
    user_ratio = user_photo.width / user_photo.height
    frame_ratio = template_w / template_h

    if user_ratio > frame_ratio:
        # نقص من العرض
        new_width = int(user_photo.height * frame_ratio)
        left = (user_photo.width - new_width) // 2
        user_photo = user_photo.crop((left, 0, left + new_width, user_photo.height))
    else:
        # نقص من الطول
        new_height = int(user_photo.width / frame_ratio)
        top = (user_photo.height - new_height) // 2
        user_photo = user_photo.crop((0, top, user_photo.width, top + new_height))

    # نكبّر الخلفية حتى تصبح بنفس حجم التومبلايت
    user_photo = user_photo.resize((template_w, template_h))

    # --- 2) نلصق التومبلايت فوق الصورة مباشرة --- #
    final_img = Image.new("RGBA", (template_w, template_h))
    final_img.paste(user_photo, (0, 0))
    final_img.paste(template, (0, 0), template)

    # حفظ النتيجة
    final_img.save(output_path)


# -------- start -------- #
@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer("👋 أرسل صورتك باللباس الكشفي.")


# -------- استقبال الصور -------- #
@dp.message(F.photo)
async def handle_photo(message: Message):
    try:
        await message.answer("⏳ جاري معالجة الصورة...")

        # تحميل صورة المستخدم
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)

        user_img_path = f"user_{message.from_user.id}.jpg"
        await bot.download_file(file_info.file_path, destination=user_img_path)

        # إنشاء الصورة النهائية
        output_path = f"final_{message.from_user.id}.png"
        create_final_image("template.png", user_img_path, output_path)

        # إرسال النتيجة
        await message.answer_photo(FSInputFile(output_path))

    except Exception as e:
        await message.answer("❌ حدث خطأ أثناء معالجة الصورة.")
        print("Error:", e)


async def main():
    print("🚀 Bot is running on Render...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
