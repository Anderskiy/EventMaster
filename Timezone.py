from disnake.ext import commands
import disnake
import asyncio
import pytz
import json

class Timezone(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timezone = None
        self.db_path = "timezone.json"


    async def load_timezone(self):
        try:
            with open(self.db_path, "r") as f:
                db = json.load(f)
        except FileNotFoundError:
            db = {}
        return db

    async def save_timezone(self):
        data = {"timezone": self.timezone.zone}
        with open(self.db_path, "w") as f:
            json.dump(data, f)

    @commands.slash_command(name="timezone", description="Устанавливает нужный часовой пояс для бота")
    async def timezone(self, inter: disnake.CommandInteraction) -> None:
        # Загрузка сохраненного часового пояса при каждом вызове команды
        await self.load_timezone()

        # Запросить у пользователя часовой пояс
        await inter.response.send_message("Пожалуйста, укажите ваш часовой пояс (например, 'Europe/Moscow').")
        try:
            # Ожидание сообщения с часовым поясом от пользователя
            timezone_message = await self.bot.wait_for('message', check=lambda m: m.author.id == inter.author.id,
                                                       timeout=60)
            timezone_str = timezone_message.content.strip()

            # Проверить, является ли введенный часовой пояс допустимым
            if timezone_str in pytz.all_timezones:
                self.timezone = pytz.timezone(timezone_str)
                await self.save_timezone()  # Сохранение часового пояса
                await inter.send(f"Установлен часовой пояс: {timezone_str}")
            else:
                await inter.send("Неверный часовой пояс. Пожалуйста, повторите попытку.")
        except asyncio.TimeoutError:
            await inter.send("Истекло время ожидания.", delete_after=10)

    @commands.slash_command(name="timezone_check", description="Проверка часового пояса")
    async def timezone_check(self, inter: disnake.CommandInteraction) -> None:
        self.load_timezone()  # Загрузка часового пояса из JSON
        if self.timezone is not None:
            await inter.send(f"Текущий часовой пояс: {self.timezone.zone}")
        else:
            await inter.send("Часовой пояс не установлен.")


def setup(bot):
    bot.add_cog(Timezone(bot))

