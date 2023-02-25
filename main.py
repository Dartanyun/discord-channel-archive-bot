import os
import re
import warnings

import emoji
import nextcord
import pandas as pd
import yadisk
from art import tprint
from dotenv import load_dotenv

load_dotenv()

warnings.simplefilter(action='ignore', category=FutureWarning)

token = os.getenv('DISCORD_BOT_TOKEN') # бот токен
y = yadisk.YaDisk(token='YANDEX_DISK_TOKEN') # после знака "=" необходимо вставить токен яндекс выданный для Яндекс.Диск REST API
super_admin = ["Admin"] # список ролей с доступом к удалению каналов через кнопку
stuff_roles = ["Admin","Help-Team"]   # список ролей с доступом к боту 
deny_roles = ["User"]  # список ролей у которых канал должен скрываться после ввода команды
client = nextcord.Client()

@client.event
def on_ready():
    '''При запуске программы выводит сообщение в консоль.'''
    tprint('VISIONLAB', font='slant')
    print('[+] Успешный вход под учтеной записью {0.user}'.format(client))
    return client.change_presence(activity=nextcord.Game('?archive help -'
                                  'помощь'))


@client.event
async def on_message(message):
    '''Основная функция'''
    if message.author == client.user:
        return
    elif message.author == "":
        return
    elif message.content.startswith('?'):

        cmd = message.content.split()[0].replace("?", "")
        if len(message.content.split()) > 1:
            parameters = message.content.split()[1:]
        # дискорд комманды
        if cmd == 'archive':

            user = message.author
            print(f'[┏] Пользователь {user} запросил доступ.')
            user_roles = []
            for role in user.roles:
                user_roles.append(role.name)   
            user_roles = ','.join(user_roles)    
            if re.search("|".join(stuff_roles), user_roles):

                print(f'[┠] Пользователь {user} имеет доступ к боту.'
                      ' Работа начата.')
                data = pd.DataFrame(columns=['Id',
                                             'Автор',
                                             'Сообщение',
                                             'Контент',
                                             'Время']
                                )

                # Определяем канал для архивации
                if len(message.channel_mentions) > 0:
                    channel = message.channel_mentions[0]
                else:
                    channel = message.channel

                # Определяем кол-во сообщений для архивации
                if (len(message.content.split()) > 1 and len(message.channel_mentions) == 0) or len(message.content.split()) > 2:
                    for parameter in parameters:
                        if parameter == "help":
                            print(f"[┠] Пользователь {user} запросил помощь по команде.")
                            roles = []
                            answer = nextcord.Embed(title="Список команд",
                                                    description="""`?archive <#channel> <number_of_messages>`\n\n`<#channel>` : **сканируемый канал**\n`<number_of_messages>` : **количество записанных сообщений**\n""",
                                                    colour=0x8167e7).set_footer(text="Developed by @Dartanyun#0515")
                            for role in stuff_roles:
                                roles.append(role)
                            roles = ', '.join(roles)                        
                            answer.add_field(name="Роли с доступом к боту:", value=f"{roles}", inline=False)                         
                            await message.channel.send(embed=answer)
                            print(f"[┗] Информация предоставлена. Конец работы.")
                            return
                        elif parameter[0] != "<": 
                            limit = int(parameter)
                else:
                    limit = 100 # настройка дефолтного лимита сообщений

                def is_command (message):
                    if len(msg.content) == 0:
                        return False
                    elif msg.content.split()[0] == '?archive':
                        return True
                    else:
                        return False         

                file_location = f"{str(channel.guild.id) + '_' + str(channel.id)}.csv" #Определение расположения файла
                filename=f"{str(channel.guild.name)+ '_#' + str(channel.name)+ '_' + str(channel.created_at.strftime('%d-%m-%Y'))}.csv"#Определение имени файла
                file_check = y.is_file(f"archivebot/{message.guild.name}/{filename}")
                if file_check == False: #проверка наличия файла в облаке

                    data = pd.DataFrame(columns=['Id','Автор','Сообщение','Контент','Время'])
                                      
                    #скрываем канал от юзеров
                    for role in stuff_roles:
                        stuff = nextcord.utils.get(message.guild.roles, name=role)
                        overwrites = channel.overwrites_for(stuff)
                        overwrites.read_messages, overwrites.send_messages = True, True
                        await channel.set_permissions(stuff, overwrite=overwrites)
                    for role in deny_roles:                 
                        users = nextcord.utils.get(message.guild.roles, name=role)
                        overwrites = channel.overwrites_for(users)
                        overwrites.read_messages, overwrites.send_messages = False, False            
                        await channel.set_permissions(users, overwrite=overwrites)
                    print(f"[┠] Канал #{channel.name} скрыт от {deny_roles}.")        

                    #создаем таблицу и заполняем её данными
                    async for msg in channel.history(limit=limit + 100,oldest_first=True):      # Добавление дополнительного лимита в случае, когда бот пропускает сообщения с инициацией команды для начала работы
                        join_attributes = ",\n"
                        attach = "NULL"
                        embed_attach = "NULL"
                        text = "NULL"
                        content = ""
                        embed_content = []
                        zxc = []
                        if msg.attachments:
                            attach = msg.attachments[0].url 
                        if msg.content:
                            content = msg.content
                            text = emoji.demojize(content)
                        elif msg.embeds:
                            embeds = msg.embeds
                            for embed in embeds:
                                zxc.append(embed.description)
                            zxc = '\n'.join(zxc)    
                            text = zxc
                            for embed in embeds:
                                if embed.image.url == nextcord.Embed.Empty:
                                    embed_content.append(embed_attach)     
                                else:    
                                    embed_content.append(embed.image.url)
                            embed_content = join_attributes.join(embed_content)    
                            attach =  embed_content        

                        if msg.author != client.user:
                                if not is_command(msg):                                           # the total amount originally specified by the user.
                                        data = data.append({'Id': int(len(data)),
                                                                'Автор': msg.author,
                                                                'Сообщение': text,
                                                                'Контент':attach,
                                                                'Время': msg.created_at.strftime('%T %d-%m-%Y')},ignore_index=True)                           
                                if len(data) == limit:
                                    break
                    print(f"[┠] Канал #{channel.name} залогирован. Попытка загрузки в облако.")                             
                    data = data.set_index('Id')           
                
                    #проверка налачия нужных папок для загрузки файла
                    dir_check = y.is_dir(f'archivebot/{message.guild.name}')
                    if dir_check == False:
                        dir_check = y.is_dir('/archivebot')
                        if dir_check == False:
                            y.mkdir('/archivebot')        
                        y.mkdir(f'archivebot/{message.guild.name}')
                        print(f'[┠]     Среда облака не подготовлена к работе с ботом. Ошибка исправлена.')

                    #проверка наличия загруженного файла с таким же именем 
                    data.to_csv(file_location) # сохраняет таблицу в csv через pandas                
                    upload_check = y.upload(file_location,f"archivebot/{message.guild.name}/{filename}")

                    result = nextcord.Embed(title=f"""Канал #{channel.name} сохраняется и архивируется""",
                                            description="Пожалуйста подожди пока сформируется и загрузится файл.",
                                            colour=0x8167e7).set_footer(text="Developed by @Dartanyun#0515") 

                    msg = await message.channel.send(embed=result)
                    if upload_check == None:

                        upload_info = nextcord.Embed(title=f"""\u2705 Канал #{channel.name} сохранен и успешно архивирован.""",
                                                    description="Удалить канал?",
                                                    colour=0x8167e7).set_footer(text="Developed by @Dartanyun#0515")

                    #кнопки для эмбеда                  
                    class DeleteButton(nextcord.ui.View):

                        #ссылка на загруженный канал
                        def __init__(self):
                            super().__init__()
                            y.publish(f"/archivebot/{message.guild.name}/{filename}")
                            filelink = y.get_meta(path=f"/archivebot/{message.guild.name}/{filename}").public_url
                            self.add_item(nextcord.ui.Button(label='Ссылка',emoji="🔗",style=nextcord.ButtonStyle.url,url=filelink)) 

                        #удаление канала через кнопку    
                        async def delete(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
                            
                            #проверка наличия роли для удаления канала
                            sar_check = []
                            for role in interaction.user.roles:
                                sar_check.append(role.name)   
                            sar_check = ','.join(sar_check)

                            if re.search("|".join(super_admin), sar_check):
                                await channel.delete()
                                button1 = [x for x in self.children if x.custom_id=="delete_button"][0]
                                button1.disabled = True
                                button1.label = "Канал был удален."
                                await interaction.response.edit_message(view=self)
                                print(f"    [┗] Пользователь {interaction.user} удалил канал #{channel}.")                       
                            else: 
                                print(f"    [┗] Пользователь {interaction.user} попытался удалить #{channel}, но у него небыло нужных прав.")
                                await interaction.response.send_message("У вас нет прав для этого действия.", ephemeral=True )    
                        
                        @nextcord.ui.button(label='Удалить', style=nextcord.ButtonStyle.danger, custom_id='delete_button')
                        async def deletebutton(self, button, interaction):
                            await self.delete(button,interaction)                                                                                               

                    await msg.edit(embed=upload_info, view=DeleteButton())
                    os.remove(file_location)#удаление файла

                    print(f"[┗] Загрузка файла {filename} в облако успешна. Работа завершена.")
                else:   
                    print("[┗] Команда не выполнена. Файл уже существует.")

                    result = nextcord.Embed(title=f"""🗃️ Лог канала #{channel.name} уже архивирован.""",
                                            description="Вы хотите перезаписать файл?",
                                            colour=0x8167e7).set_footer(text="Developed by @Dartanyun#0515") 

                    class ReuploadButton(nextcord.ui.View):     

                        #перезапись канала через кнопку    
                        async def reupload(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
                            table = pd.DataFrame(columns=['Id','Автор','Сообщение','Контент','Время'])

                            def is_command (message):
                                if len(msg.content) == 0:
                                    return False
                                elif msg.content.split()[0] == '?archive':
                                    return True
                                else:
                                    return False     

                            #создаем таблицу и заполняем её данными
                            async for msg in channel.history(limit=limit + 100,oldest_first=True): # Добавление дополнительного лимита в случае, когда бот пропускает сообщения с инициацией команды для начала работы
                                join_attributes = ",\n"
                                attach = "NULL"
                                embed_attach = "NULL"
                                text = "NULL"
                                content = ""
                                embed_content = []
                                zxc = []
                                if msg.attachments:
                                    attach = msg.attachments[0].url 
                                if msg.content:
                                    content = msg.content
                                    text = emoji.demojize(content)
                                elif msg.embeds:
                                    embeds = msg.embeds
                                    for embed in embeds:
                                        zxc.append(embed.description)
                                    zxc = '\n'.join(zxc)    
                                    text = zxc
                                    for embed in embeds:
                                        if embed.image.url == nextcord.Embed.Empty:
                                            embed_content.append(embed_attach)     
                                        else:    
                                            embed_content.append(embed.image.url)
                                    embed_content = join_attributes.join(embed_content)    
                                    attach =  embed_content

                                if msg.author != client.user:
                                        if not is_command(msg):                                           # the total amount originally specified by the user.
                                                table = table.append({'Id': int(len(table)),
                                                                    'Автор': msg.author,
                                                                    'Сообщение': text,
                                                                    'Контент':attach,
                                                                    'Время': msg.created_at.strftime('%T %d-%m-%Y')},ignore_index=True)                           
                                        if len(table) == limit:
                                            break         
                            table = table.set_index('Id')                                 
                            table.to_csv(file_location)                                    
                            button1 = [x for x in self.children if x.custom_id=="reupload_button"][0]
                            button1.disabled = True
                            button1.label = "Канал был перезаписан."
                            button1.emoji = None
                            await interaction.response.edit_message(view=self)                            
                            upload_check = y.upload(file_location,f"archivebot/{message.guild.name}/{filename}" , overwrite=True)
                            os.remove(file_location)#удаление файла

                            if upload_check == None:

                                print(f"    [┗] Пользователь {interaction.user} перезаписал канал #{channel}.")  

                        #удаление канала через кнопку    
                        async def delete(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):

                            sar_check = []
                            for role in interaction.user.roles:
                                sar_check.append(role.name)   
                            sar_check = ','.join(sar_check)

                            #проверка наличия роли для удаления канала
                            if re.search("|".join(super_admin), sar_check):
                                await channel.delete()
                                button1 = [x for x in self.children if x.custom_id=="delete_button"][0]
                                button1.disabled = True
                                button1.label = "Канал был удален."
                                await interaction.response.edit_message(view=self)
                                print(f"    [┗] Пользователь {interaction.user} удалил канал #{channel}.")                                
                            else: 
                                print(f"    [┗] Пользователь {interaction.user} попытался удалить #{channel}, но у него небыло нужных прав.")
                                await interaction.response.send_message("У вас нет прав для этого действия.", ephemeral=True )
                        
                        @nextcord.ui.button(label='Удалить', style=nextcord.ButtonStyle.danger, custom_id='delete_button')
                        async def deletebutton(self, button, interaction):
                            await self.delete(button,interaction)       

                        @nextcord.ui.button(label='Перезаписать', style=nextcord.ButtonStyle.green, emoji="♻️", custom_id='reupload_button')
                        async def deletebutton(self, button, interaction):
                            await self.reupload(button,interaction) 
                        
                        #ссылка на загруженный канал
                        def __init__(self):
                            super().__init__()
                            y.publish(f"/archivebot/{message.guild.name}/{filename}")
                            filelink = y.get_meta(path=f"/archivebot/{message.guild.name}/{filename}").public_url
                            self.add_item(nextcord.ui.Button(label='Ссылка', emoji="🔗", style=nextcord.ButtonStyle.url, url=filelink))                                                                                                                                                                            

                    msg = await message.channel.send(embed=result, view=ReuploadButton())
            else:
                print(f'[┗] Отказ в доступе. Пользователь {user} пытался инициализировать команду , но не имел роли из списка доступа.')
                return

client.run(token)