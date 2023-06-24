import disnake, rgbprint, aiohttp, asyncio, time, json, os, math, socketio, uuid, datetime
from disnake.ext import commands

SocketIOClient = socketio.AsyncClient(reconnection = False)

activity = disnake.Activity(name='hi chat 🐱', type=disnake.ActivityType.competing)
bot = commands.Bot(command_prefix=commands.when_mentioned, activity=activity)

firstcolor = 0xDEE7F5
maincolor = 0x6290CA

class Sniper:
    def __init__(self) -> None:
        self.online = 0
        self.bought = 0
        self.lastbought = None
        
        self.isconnected = False
        self.connectlatency = 0
        self.lastauto = None

        self.errors = 0
        self.latency = 0
        self.checks = 0
        
        self.config = self.read_config()
        self.items = self.config.get("WATCHER")
        self.deaditems = []
        self.accounts = []

        self.key = self.config.get("KEY")
        self.running = round(time.time())

        @SocketIOClient.event
        async def connect():
            self.isconnected = True
            print("connected to server")

        @SocketIOClient.event
        async def heartbeat(sid):
            self.online = sid
            #print("online: ", self.online)

        @SocketIOClient.event
        async def freelimited(itemdata):
            print(itemdata)
            if itemdata not in self.deaditems:
                self.deaditems.append(itemdata)
                itemdata = await self.get_item(self.accounts[0], itemdata)
                cour = []
                print(itemdata)
                self.lastauto = itemdata.get("Name")
                if itemdata.get("PriceInRobux") != None and itemdata.get("PriceInRobux") == 0:
                    for account in self.accounts:
                        cour.append(self.buy_item(itemdata, account))
                    await asyncio.gather(*cour)

        @SocketIOClient.event
        async def disconnect():
            self.isconnected = False
            print("disconnected to server")

        if self.config.get("DISCORD").get("ENABLE"):
            self.discord_bot()
        else:
            asyncio.run(self.run())

    def discord_bot(self):
        @bot.event
        async def on_ready():
            print(f"Logged in as {bot.user} (ID: {bot.user.id})\n------")
            await self.run()

        @bot.slash_command(name="stats", description="Prints all stats from console")
        async def discordprintstats(inter):
            if inter.author.id not in self.config.get("DISCORD").get("AUTHORIZED_IDS"):
                await inter.response.send_message("😦", delete_after=5, ephemeral=True)
            else:
                embed=disnake.Embed(title="mewted", color = maincolor)
                embed.set_image(url="https://0w0.discowd.com/r/mewted.png")
                embed.add_field(name="Main", value=f"👥 \> Online Users: {self.online} \n💸 \> Bought: {self.bought} \n✨ \> Last Bought: {self.lastbought}", inline=False)
                embed.add_field(name="Autosearch", value=f"📡 \> Connected: {self.isconnected} \n⏱️ > Latency: {self.connectlatency} \n🔍 > Last Detected: {self.lastauto}", inline=False)
                embed.add_field(name="Watcher", value=f"❌ > Errors: {self.errors} \n⏱️ > Latency: {self.latency} \n👀 > Checks: {self.checks}", inline=False)
                await inter.response.send_message("", embed= embed)

        @bot.slash_command(name="get_watcher", description="Give lists of limiteds in watcher")
        async def discordlistwatcher(inter):
            if inter.author.id not in self.config.get("DISCORD").get("AUTHORIZED_IDS"):
                await inter.response.send_message("😦", delete_after=5, ephemeral=True)
            else:
                await inter.response.send_message(f"{self.items}")
        
        @bot.slash_command(name="remove_watcher", description="Removes limited id from watcher")
        async def discordremovewatcher(inter, assetid: str = commands.Param(description="Limited id")):
            if inter.author.id not in self.config.get("DISCORD").get("AUTHORIZED_IDS"):
                await inter.response.send_message("😦", delete_after=5, ephemeral=True)
            else:
                try:
                    self.items.remove(int(assetid))
                    await inter.response.send_message(f"Removed {assetid} from list :innocent:")
                except:
                    await inter.response.send_message(f"Couldn't find that item in list 🙁")
                    
        
        @bot.slash_command(name="add_watcher", description="Adds limited id in watcher")
        async def discordaddwatcher(inter, assetid: str = commands.Param(description="Limited id")):
            if inter.author.id not in self.config.get("DISCORD").get("AUTHORIZED_IDS"):
                await inter.response.send_message("😦", delete_after=5, ephemeral=True)
            else:
                async with aiohttp.ClientSession(cookies={".ROBLOSECURITY": self.accounts[0].get("cookie")}) as client:
                        async with client.get(f"https://economy.roblox.com/v2/assets/{assetid}/details", ssl = False) as response:
                            
                            rq = await response.json()
                            if int(assetid) in self.items:
                                await inter.response.send_message(f"{rq['Name']} already in watchlist :neutral_face:")
                            else:
                                self.items.append(int(assetid))
                                await inter.response.send_message(f"Added {rq['Name']} to watchlist :innocent:")

        bot.run(self.config.get("DISCORD").get("TOKEN"))

    def read_config(self) -> None:
        with open('config.json', "r") as f:
            return json.load(f)
    
    def _print_stats(self) -> None:
        os.system("cls")
        rgbprint.gradient_print("""
                                                                 d8b 
                                               d8P               88P 
                                            d888888P            d88  
          88bd8b,d88b  d8888b ?88   d8P  d8P  ?88'   d8888b d888888  
          88P'`?8P'?8bd8b_,dP d88  d8P' d8P'  88P   d8b_,dPd8P' ?88  
         d88  d88  88P88b     ?8b ,88b ,88'   88b   88b    88b  ,88b 
        d88' d88'  88b`?888P' `?888P'888P'    `?8b  `?888P'`?88P'`88b
                                                             

                         hi chat - crack by 303                          
                                            
        """, start_color=firstcolor, end_color=maincolor)   
        users = []
        for user in self.accounts:
            users.append(user.get("name"))
        print(f"{rgbprint.Color(0xFFFFFF)}>> Current User: {rgbprint.Color(maincolor)}{users}")
        print(f"{rgbprint.Color(0xFFFFFF)}> Online Users: {rgbprint.Color(maincolor)}{self.online}")
        print(f"{rgbprint.Color(0xFFFFFF)}> Bought: {rgbprint.Color(maincolor)}{self.bought}")
        print(f"{rgbprint.Color(0xFFFFFF)}> Last Bought: {rgbprint.Color(maincolor)}{self.lastbought}")
        print()
        print(f"{rgbprint.Color(0xFFFFFF)}>> Autosearch")
        print(f"{rgbprint.Color(0xFFFFFF)}> Connected: {rgbprint.Color(maincolor)}{self.isconnected}")
        print(f"{rgbprint.Color(0xFFFFFF)}> Latency: {rgbprint.Color(maincolor)}{self.connectlatency}")
        print(f"{rgbprint.Color(0xFFFFFF)}> Last Detected: {rgbprint.Color(maincolor)}{self.lastauto}")
        print()
        print(f"{rgbprint.Color(0xFFFFFF)}-> Watcher")
        print(f"{rgbprint.Color(0xFFFFFF)}> Errors: {rgbprint.Color(maincolor)}{self.errors}")
        print(f"{rgbprint.Color(0xFFFFFF)}> Latency: {rgbprint.Color(maincolor)}{self.latency}")
        print(f"{rgbprint.Color(0xFFFFFF)}> Checks: {rgbprint.Color(maincolor)}{self.checks}")
        print()
        s = round(time.time()) - self.running
        m = math.floor(s/60)
        s -= m*60
        h = math.floor(m/60)
        m -= h*60
        print(f"{rgbprint.Color(0xFFFFFF)}> Run Time: {rgbprint.Color(maincolor)}{'0' if len(str(h))==1 else ''}{h}:{'0' if len(str(m))==1 else ''}{m}:{'0' if len(str(s))==1 else ''}{s}")
        print(f"{rgbprint.Color(0xFFFFFF)}> Watching: {rgbprint.Color(maincolor)}{self.items}")
    
    async def get_item(self, account, collectableId):
        async with aiohttp.ClientSession() as client:
            productid_data1 = await client.post("https://apis.roblox.com/marketplace-items/v1/items/details",
                         json={"itemIds": [collectableId]},
                         headers={"x-csrf-token": account.get("token"), 'Accept': "application/json"},
                         cookies={".ROBLOSECURITY": account.get("cookie")}, ssl = False)
            
            if productid_data1.status != 200:
                productid_data1 = await client.post("https://apis.roblox.com/marketplace-items/v1/items/details",
                         json={"itemIds": [collectableId]},
                         headers={"x-csrf-token": account.get("token"), 'Accept': "application/json"},
                         cookies={".ROBLOSECURITY": account.get("cookie")}, ssl = False)
            
            #print(productid_data1.status)
            productid_data = await productid_data1.json()
            productid_data = productid_data[0]

            itemdata = {"AssetId":productid_data["itemTargetId"], "CollectibleItemId":collectableId, "CollectibleProductId":productid_data["collectibleProductId"], "Name": productid_data['name'], "Creator": {"CreatorTargetId": productid_data["creatorId"], "Name": productid_data["creatorName"], "Id": productid_data["creatorId"], "CreatorType": productid_data["creatorType"]}, "Remaining":productid_data["unitsAvailableForConsumption"], "PriceInRobux":productid_data["price"], "Description":productid_data["description"]}
            return itemdata

    async def CheckServer(self) -> None:
        while True:
            if SocketIOClient.get_sid() is None:
                try:
                    t1 = time.time()
                    await SocketIOClient.connect("http://", headers={"key": self.key})
                    t2 = time.time()
                    self.connectlatency = round(t2-t1, 2)
                except Exception as e:
                    await SocketIOClient.disconnect()
                    print("Error CheckServer",e)
                    
            await asyncio.sleep(1)
    
    async def auto_update(self):
        while True:
            self._print_stats()
            await asyncio.sleep(1)

    async def buy_item(self, itemdata, account):
        data = {
            "collectibleItemId": itemdata["CollectibleItemId"],
            "expectedCurrency": 1,
            "expectedPrice": 0,
            "expectedPurchaserId": account["id"],
            "expectedPurchaserType": "User",
            "expectedSellerId": itemdata["Creator"]["Id"],
            "expectedSellerType": itemdata["Creator"]["CreatorType"],
            "idempotencyKey": str(uuid.uuid4()),
            "collectibleProductId": itemdata["CollectibleProductId"]
        }

        
        async with aiohttp.ClientSession() as client:
                response = await client.post(f"https://apis.roblox.com/marketplace-sales/v1/item/{itemdata['CollectibleItemId']}/purchase-item",
                        json=data,
                        headers={"x-csrf-token": account["token"]},
                        cookies={".ROBLOSECURITY": account["cookie"]}, ssl = False)
                rq = await response.json()
                print(rq)
                if response.status != 200:
                    self.errors += 1
                elif rq.get("errorMessage") != None:
                    self.errors += 1
                    print(rq.get("errorMessage"))
                elif rq.get("purchased") != None and rq.get("purchased") == False:
                    self.errors += 1
                    print(rq)
                else:
                    self.bought += 1
                    self.lastbought = itemdata["Name"]
                    if self.config.get("WEBHOOK") != None and self.config.get("WEBHOOK") != "":
                        ttime = datetime.datetime.utcnow()
                        try:
                            itemdataa = await client.get(f"https://economy.roblox.com/v2/assets/{itemdata['AssetId']}/details")
                            itemdataa = await itemdataa.json()
                            serialjson = await client.get(f"https://inventory.roblox.com/v2/users/{account.get('id')}/inventory/{itemdataa.get('AssetTypeId')}?limit=10&sortOrder=Desc",
                                                               headers={"x-csrf-token": account["token"]},
                                                               cookies={".ROBLOSECURITY": account["cookie"]}, ssl = False)
                            serialjson = await serialjson.json()
                            serials = []
                            for item in serialjson.get("data"):
                                if item.get("assetId") == itemdataa.get("AssetId"):
                                    serials.append(item.get("serialNumber"))
                        except:
                            serials = "epic ratelimit"
                            self.errors += 1
                        
                        webhookjson = {
                            "embeds": [
                                {
                                "title": "Sniped with mewted",
                                "url": f"https://www.roblox.com/catalog/{itemdata['AssetId']}",
                                "color": 0x000000,
                                "fields": [
                                    {
                                    "name": "Name",
                                    "value": itemdata["Name"]
                                    },
                                    {
                                    "name": "Remaining",
                                    "value": itemdata["Remaining"]
                                    },
                                    {
                                    "name": "Price",
                                    "value": itemdata["PriceInRobux"]
                                    }
                                ],
                                "author": {
                                    "name": account.get("name"),
                                    "url": f"https://www.roblox.com/users/{account.get('id')}"
                                },
                                "footer": {
                                    "text": f"Serials: {serials}"
                                },
                                "timestamp": ttime.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                                "thumbnail": {
                                    "url": "https://0w0.discowd.com/r/mewted.png"
                                }
                                }
                            ],
                            "attachments": []
                            }
                        
                        whrsp = await client.post(self.config.get("WEBHOOK"), json=webhookjson)
                        await asyncio.sleep(self.config.get('BUY_DEBOUNCE'))


    async def get_user(self, account):
        async with aiohttp.ClientSession(cookies={".ROBLOSECURITY": account["cookie"]}) as client:
                async with client.get("https://users.roblox.com/v1/users/authenticated", ssl = False) as response:
                    userjson = await response.json()
                    account["id"] = userjson.get("id")
                    account["name"] = userjson.get("name")
        
        return account

    async def update_token(self, account):
        while True:
            try:
                async with aiohttp.ClientSession(cookies={".ROBLOSECURITY": account["cookie"]}) as client:
                    async with client.post("https://accountsettings.roblox.com/v1/email", ssl = False) as response:
                        xcsrf_token = response.headers.get("x-csrf-token")
                        account["token"] = xcsrf_token
                        if xcsrf_token is None:
                            raise Exception("X-Token не получен, неверный куки.")
            except:
                print("something went wrong with token updating")
                self.errors += 1
                
            await asyncio.sleep(1)
    
    async def watcher(self):
        while True:
            if len(self.items) != 0:
                try:
                    for item in self.items:
                        t1 = time.time()
                        async with aiohttp.ClientSession(cookies={".ROBLOSECURITY": self.accounts[0].get("cookie")}) as client:
                            async with client.get(f"https://economy.roblox.com/v2/assets/{item}/details", ssl = False) as response:
                                #print(response)
                                t2 = time.time()
                                self.latency = round(t2-t1, 2)
                                if response.status != 200:
                                    self.errors += 1
                                    pass
                                else:
                                    self.checks += 1
                                    rq = await response.json()
                                    if rq.get("Remaining") != 0 and rq.get("PriceInRobux") == 0:
                                        print("economy")
                                        temp = []
                                        for account in self.accounts:
                                            temp.append(self.buy_item(rq, account))
                                        await asyncio.gather(*temp)
                                    elif rq.get("PriceInRobux") != None and rq.get("PriceInRobux") != 0:
                                        self.items.remove(int(item))
                                    elif rq.get("Remaining") == 0:
                                        self.items.remove(int(item))
                except:
                    self.errors += 1
                    print("something went wrong with watcher")
                    await asyncio.sleep(5)
            else:
                await asyncio.sleep(1)
     
    async def run(self):
        self.items = self.config.get("WATCHER")

        coroutines = []
        if self.config.get("AUTOSEARCH"):
            coroutines.append(self.CheckServer())

        if not self.config.get("DEBUG"):
            coroutines.append(self.auto_update())

        for cookie in self.config.get("AUTHENTICATION").get("COOKIES"):
            account = {} 
            account["cookie"] = cookie
            account = await self.get_user(account)
            if account.get("name") != None:
                coroutines.append(self.update_token(account))
                self.accounts.append(account)
            else:
                self.errors += 1
                print("Invalid cookie")
                
        coroutines.append(self.watcher())
        
        await asyncio.gather(*coroutines)

Sniper()
