import disnake
from disnake.ext import commands
from disnake.enums import GuildScheduledEventEntityType, GuildScheduledEventPrivacyLevel
from datetime import datetime
import datetime
import asyncio

allowed_roles = [921086089924579461, 1051045728283267073, 857667728055992400, 1085421304804540416, 1108439880289239171]  # Список разрешенных ролей
channel_id_metion = 1064404769227149332
role_ping_id = 1108439880289239171

class ConfirmationButtons(disnake.ui.View):
    def __init__(self, author, name, description, scheduled_start_time, channel, image_data):
        super().__init__()
        self.author = author
        self.name = name
        self.description = description
        self.scheduled_start_time = scheduled_start_time
        self.channel = channel
        self.image_data = image_data

    @disnake.ui.button(label='Подтвердить', style=disnake.ButtonStyle.green)
    async def confirm(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if interaction.user.id == self.author.id:
            await self.do_action(interaction, True)

    @disnake.ui.button(label='Отмена', style=disnake.ButtonStyle.red)
    async def cancel(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if interaction.user.id == self.author.id:
            await self.do_action(interaction, False)

    async def do_action(self, interaction: disnake.MessageInteraction, confirmed: bool):
        if confirmed:
            await interaction.response.defer()
            try:
                if self.image_data is None:
                    created_gse = await interaction.guild.create_scheduled_event(
                        name=self.name,
                        description=self.description if self.description is not None else "",
                        privacy_level=GuildScheduledEventPrivacyLevel.guild_only,
                        scheduled_start_time=self.scheduled_start_time,
                        entity_type=GuildScheduledEventEntityType.voice,
                        channel=self.channel,
                    )
                else:
                    created_gse = await interaction.guild.create_scheduled_event(
                        name=self.name,
                        description=self.description if self.description is not None else "",
                        privacy_level=GuildScheduledEventPrivacyLevel.guild_only,
                        scheduled_start_time=self.scheduled_start_time,
                        entity_type=GuildScheduledEventEntityType.voice,
                        channel=self.channel,
                        image=self.image_data if self.image_data is not None else b"",
                    )
                await interaction.followup.send(f'Ивент **{created_gse.name}** (ID: {created_gse.id}) создан!')
            except Exception as e:
                await interaction.followup.send(f'Ошибка при создании ивента: {str(e)}', ephemeral=True)
        else:
            await interaction.send("Создание ивента отклонено")
            await asyncio.sleep(20)
            await interaction.message.delete(delete_after=22)

class CreateEvets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timezones = {}

    @commands.slash_command(name="set_channel_public", description="Установить публичный канал")
    async def set_public_channel(
            self, inter: disnake.GuildCommandInteraction, channel: disnake.TextChannel
    ) -> None:
        global channel_id_metion
        channel_id_metion = channel.id
        await inter.response.send_message(f"Установлен публичный канал: <#{channel_id_metion}>")

    @commands.slash_command(name="set_role_ping", description="Установить пингуемую роль")
    async def role_ping_set(
            self, inter: disnake.GuildCommandInteraction, role: disnake.Role
    ) -> None:
        global role_ping_id
        role_ping_id = role.id
        await inter.response.send_message(f"Установлен публичный канал: {role.name}")

    @commands.slash_command(name="event_end", description="Заканчивает ивент")
    async def end_event(
            self, inter: disnake.GuildCommandInteraction, id: commands.LargeInt
    ) -> None:
        gse = await inter.guild.fetch_scheduled_event(id)
        if gse:  # Проверяем, что пользователь является создателем ивента

            creator_id = gse.creator.id
            member = inter.author
            # Проверяем, что пользователь является создателем ивента или имеет разрешенную роль
            if member.id == creator_id or any(role.id in allowed_roles for role in member.roles):

                await inter.response.defer()
                await gse.end()  # Заканчиваем ивент
                await inter.send(f"Ивент **{gse.name}** окончен!")

            else:
                await inter.response.send_message("Вы не являетесь создателем данного ивента.", ephemeral=True)
        else:
            await inter.response.send_message("Не удалось найти ивент с указанным идентификатором.", ephemeral=True)

    @commands.slash_command(name="event_start", description="Начинает ивент")
    async def start_event(
            self, inter: disnake.GuildCommandInteraction, id: commands.LargeInt
    ) -> None:
        gse = await inter.guild.fetch_scheduled_event(id)
        if gse:  # Проверяем, что пользователь является создателем ивента
            creator_id = gse.creator.id
            member = inter.author

            # Проверяем, что пользователь является создателем ивента или имеет разрешенную роль
            if member.id == creator_id or any(role.id in allowed_roles for role in member.roles):

                await inter.response.defer()
                await gse.start()  # Начинаем ивент
                await inter.send(f"Ивент **{gse.name}** начат!")
                channel = inter.guild.get_channel(channel_id_metion)
                await channel.send(f"<@&{role_ping_id}> \nИвент **{gse.name}** начат! \n{gse.url}",
                                   delete_after=300)
            else:
                await inter.response.send_message("Вы не являетесь создателем данного ивента.", ephemeral=True)
        else:
            await inter.response.send_message("Не удалось найти ивент с указанным идентификатором.", ephemeral=True)

    @commands.slash_command(name='event_edit', description='Редактирует существующий ивент')
    async def edit_event(self, inter: disnake.GuildCommandInteraction, id: commands.LargeInt,
            name: str = None, description: str = None, image: disnake.Attachment = None,
            date: str = None, time: str = None
    ) -> None:
        await inter.response.defer()

        # Проверка наличия правильного ID ивента
        gse = await inter.guild.fetch_scheduled_event(id)
        if not gse:
            await inter.response.send_message(f'Ивент с ID {gse.id} не найден.', ephemeral=True)
            return

        if gse.entity_type == 'external':
            if gse.scheduled_end_time is None:
                # Установите время окончания события для внешних событий
                # Например, если время начала задано в scheduled_start_time, вы можете добавить один час к нему:
                gse.scheduled_end_time = gse.scheduled_start_time + datetime.timedelta(hours=1)

        if name:
            gse.name = name
        if description:
            gse.description = description
        if image:
            await gse.edit(image=await image.read())
        if date and time:
            try:
                scheduled_date = datetime.datetime.strptime(date, "%d.%m").date()
                scheduled_date = scheduled_date.replace(year=datetime.datetime.utcnow().year)
                scheduled_time = datetime.datetime.strptime(time, "%H:%M").time()
                scheduled_start_time = datetime.datetime.combine(scheduled_date, scheduled_time)
                gse.scheduled_start_time = scheduled_start_time
            except ValueError:
                await inter.send("Неверный формат даты или времени.", ephemeral=True)
                return

        try:
            # Сохранение обновленного ивента
            await gse.edit(name=gse.name, description=gse.description, scheduled_start_time=gse.scheduled_start_time)
            await inter.send(f"Ивент с ID {gse.id} успешно отредактирован!")
        except Exception as e:
            await inter.send(f"Ошибка при редактировании ивента: {str(e)}", ephemeral=True)

    @commands.slash_command(name="event_info", description="Показывает информаацию насчет ивента")
    async def fetch_event(
            self, inter: disnake.GuildCommandInteraction, id: commands.LargeInt
    ) -> None:
        gse = await inter.guild.fetch_scheduled_event(id)
        scheduled_start_time_str = f"<t:{int(gse.scheduled_start_time.timestamp())}:F>"
        embed = disnake.Embed(title=f"Название: {gse.name}", color=0x2B2D31)
        embed.add_field(name='Описание ивента:', value=gse.description, inline=False)
        embed.add_field(name='Дата начала:', value=scheduled_start_time_str, inline=False)
        embed.add_field(name='Канал проведения:', value=gse.channel, inline=False)
        embed.set_image(url=gse.image.url)  # Устанавливаем изображение в виде миниатюры
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="event_create", description="Создает кастомный ивент на сервере")
    async def create_event(
            self, inter: disnake.GuildCommandInteraction, name: str, channel: disnake.VoiceChannel,
            date: str, time: str, description: str = None, image: disnake.Attachment = None
    ) -> None:
        image_data = None
        if image:
            image_data = await image.read()

        description = None
        if description:
            description = description

        # Обработка введенной даты
        try:
            scheduled_date = datetime.datetime.strptime(date, "%d.%m").date()
            scheduled_date = scheduled_date.replace(year=datetime.datetime.utcnow().year)  # Заменяем год на текущий
        except ValueError:
            await inter.response.send_message("Неверный формат даты. Используйте дд.мм", ephemeral=True)
            return

        # Обработка введенного времени
        try:
            scheduled_time = datetime.datetime.strptime(time, "%H:%M").time()
        except ValueError:
            await inter.response.send_message("Неверный формат времени. Используйте чч:мм", ephemeral=True)
            return

        # Комбинирование даты и времени в один объект datetime
        scheduled_start_time = datetime.datetime.combine(scheduled_date, scheduled_time)

        # Создание строки временной отметки времени в формате Discord
        scheduled_start_time_str = f"<t:{int(scheduled_start_time.timestamp())}:F>"

        embed = disnake.Embed(title=f"Название: {name}", color=0x2B2D31)
        if description is not None:
            embed.add_field(name='Описание ивента:', value=description, inline=False)
        embed.add_field(name='Дата начала:', value=scheduled_start_time_str, inline=False)
        embed.add_field(name='Канал проведения:', value=channel, inline=False)
        if image is not None:
            embed.set_image(url=image.url)
        confirmation_view = ConfirmationButtons(
            inter.author, name, description, scheduled_start_time, channel, image_data
        )
        await inter.response.send_message(embed=embed, view=confirmation_view)

def setup(bot):
    bot.add_cog(CreateEvets(bot))
