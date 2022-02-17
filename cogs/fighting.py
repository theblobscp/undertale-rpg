import asyncio
import random
import time

import discord
from discord.ext import commands
from dislash import *

import botTools.loader as loader


class Fight(commands.Cog):
    def __init_(self, bot):
        self.bot = bot

    @commands.command(aliases=["bossfight"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def fboss(self, ctx):
        """Fight Bosses and gain EXP and Gold"""
        ctx.message.content = "u?boss"
        await ctx.bot.process_commands(ctx.message)

    @commands.command(aliases=["f", "boss"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def fight(self, ctx):
        """Fight Monsters and gain EXP and Gold"""
        await loader.create_player_info(ctx, ctx.author)
        data = await ctx.bot.players.find_one({"_id": ctx.author.id})
        cmd_list = ["fboss", "bossfight", "boss"]
        if ctx.invoked_with in cmd_list:
            curr_time = time.time()
            delta = float(curr_time) - float(data["rest_block"])

            if delta <= 1800.0 and delta > 0:
                seconds = 1800 - delta
                m, s = divmod(seconds, 60)
                h, m = divmod(m, 60)
                em = discord.Embed(
                    description=f"**You can't fight a boss yet!**\n\n**You can fight a boss <t:{int(time.time()) + int(seconds)}:R>**",
                    color=discord.Color.red(),
                )
                em.set_thumbnail(
                    url="https://cdn.discordapp.com/attachments/850983850665836544/878024511302271056/image0.png"
                )
                await ctx.send(embed=em)
                return

        if data["fighting"]:
            return

        location = data["location"]
        rand_monst = []
        info = None

        for i in ctx.bot.monsters:
            if ctx.bot.monsters[i]["location"] == location:
                if ctx.bot.monsters[i]["boss"] and ctx.invoked_with in cmd_list:
                    rand_monst.append(i)
                elif (
                        ctx.bot.monsters[i]["boss"] is False
                        and ctx.invoked_with not in cmd_list
                ):
                    rand_monst.append(i)
                else:
                    pass

        info = ctx.bot.monsters

        if len(rand_monst) == 0:
            await ctx.send(f"There are no monsters here?, Are you in an only boss area?, {ctx.prefix}boss")
            return
        monster = random.choice(rand_monst)
        row = ActionRow(
            Button(style=ButtonStyle.green, label="Yes", custom_id="yes"),
            Button(style=ButtonStyle.red, label="No", custom_id="no"),
        )

        mon_hp_min = info[monster]["min_hp"]
        mon_hp_max = info[monster]["max_hp"]
        damage = info[monster]["atk"]
        # image = einfo[elocation]["enemies"][monster]["image"]
        # embed.set_thumbnail(url=image)
        enemy_hp = random.randint(mon_hp_min, mon_hp_max)

        health = data["health"]
        title = info[monster]["title"]

        embed = discord.Embed(
            title=f"{monster}, {title}",
            description=f"**Your HP is {health}\nMonster health: {enemy_hp}HP\ncan deal up to {damage}ATK**",
            color=discord.Colour.blue(),
        )

        msg = await ctx.send(ctx.author.mention, embed=embed, components=[row])

        on_click = msg.create_click_listener(timeout=30)

        @on_click.not_from_user(ctx.author, cancel_others=True, reset_timeout=False)
        async def on_wrong_user(inter):
            # Reply with a hidden message
            await inter.reply("This is not yours kiddo!", ephemeral=True)

        @on_click.matching_id("no")
        async def on_test_button(inter, reset_timeout=False):
            embed.description += "\n\n**You Flee'd**"
            ctx.command.reset_cooldown(ctx)
            new = []
            row.disable_buttons()
            await msg.edit(components=[row])
            await inter.reply("You fleed", ephemeral=True)
            on_click.kill()
            return

        @on_click.matching_id("yes")
        async def on_test_button(inter, reset_timeout=False):
            await msg.edit(components=[])
            on_click.kill()

            data = {
                "selected_monster": monster,
                "monster_hp": enemy_hp,
                "fighting": True,
                "last_monster": monster
            }

            await ctx.bot.players.update_one({"_id": ctx.author.id}, {"$set": data})
            print(f"{ctx.author} has entered a fight")
            return await Menu.menu(self, ctx)

        @on_click.timeout
        async def on_timeout():
            row.disable_buttons()
            embed.description += "\n\nYou took too much to reply!"
            await msg.edit(embed=embed, components=[row])


def setup(bot):
    bot.add_cog(Fight(bot))


class Core:
    async def get_bar(health, max_health):
        bar0 = "<:0_:899376245496758343>"
        bar1 = "<:1_:899376320079855656>"
        bar2 = "<:2_:899376429568000040>"
        bar3 = "<:3_:899376559700451379>"
        bar4 = "<:4_:899376608220172339>"
        bar5 = "<:5_:899376657759088750>"
        bar = None
        mix = health / max_health
        per = mix * 100
        if per == 0:
            bar = f"{bar0}{bar0}{bar0}{bar0}{bar0}"
        if per <= 10 and per > 0:
            bar = f"{bar2}{bar0}{bar0}{bar0}{bar0}"
        if per <= 20 and per > 10:
            bar = f"{bar5}{bar0}{bar0}{bar0}{bar0}"
        if per <= 30 and per > 20:
            bar = f"{bar5}{bar2}{bar0}{bar0}{bar0}"
        if per <= 40 and per > 30:
            bar = f"{bar5}{bar4}{bar0}{bar0}{bar0}"
        if per <= 50 and per > 40:
            bar = f"{bar5}{bar5}{bar2}{bar0}{bar0}"
        if per <= 60 and per > 50:
            bar = f"{bar5}{bar5}{bar4}{bar0}{bar0}"
        if per <= 70 and per > 60:
            bar = f"{bar5}{bar5}{bar5}{bar3}{bar0}"
        if per <= 80 and per > 70:
            bar = f"{bar5}{bar5}{bar5}{bar5}{bar2}"
        if per <= 90 and per > 80:
            bar = f"{bar5}{bar5}{bar5}{bar5}{bar4}"
        if per <= 100 and per > 90:
            bar = f"{bar5}{bar5}{bar5}{bar5}{bar5}"
        return bar

    async def count(store, value):
        try:
            store[value] = store[value] + 1
        except KeyError as e:
            store[value] = 1
            return

    async def _check_levelup(self, ctx):
        author = ctx.author
        info = await ctx.bot.players.find_one({"_id": author.id})
        xp = info["exp"]
        num = 100
        lvl = info["level"]
        lvlexp = num * lvl
        if xp >= lvlexp:
            info["level"] = info["level"] + 1
            info["max_health"] = info["max_health"] + 4
            new_lvl = info["level"]
            new_dmg = info["damage"]

            data = {
                "level": info["level"],
                "exp": xp - lvlexp,
                "max_health": info["max_health"] + 4,
                "damage": info["damage"] + 1
            }
            await ctx.bot.players.update_one({"_id": author.id}, {"$set": data})
            embed = discord.Embed(
                title="LOVE Increased",
                description=f"Your LOVE Increased to **{new_lvl}**\nDamage increased to {new_dmg}",
                color=discord.Colour.red(),
            )
            await ctx.send(ctx.author.mention, embed=embed)
            for i in ctx.bot.locations:
                if ctx.bot.locations[i]["RQ_LV"] == info["level"]:
                    await ctx.send(
                        f"Congrats, You unlocked {i}, you can go there by running {ctx.prefix}travel"
                    )
            return await Core._check_levelup(self, ctx)
        else:
            return


class Menu:
    async def menu(self, ctx):
        info = await ctx.bot.players.find_one({"_id": ctx.author.id})
        row = ActionRow(
            Button(style=ButtonStyle.red, label="Fight", custom_id="fight"),
            # Button(style=ButtonStyle.gray, label="Act", custom_id="act"),
            Button(style=ButtonStyle.gray, label="Items", custom_id="items"),
            Button(style=ButtonStyle.green, label="mercy", custom_id="spare"),
        )

        player = ctx.author
        embed = discord.Embed(title="Choose an Option:", color=discord.Colour.red())
        msg = await ctx.send(player.mention, embed=embed, components=[row])
        on_click = msg.create_click_listener(timeout=120)
        row.disable_buttons()

        @on_click.not_from_user(ctx.author, cancel_others=True, reset_timeout=False)
        async def on_wrong_user(inter):
            # Reply with a hidden message
            await inter.reply("This is not yours kiddo!", ephemeral=True)

        @on_click.matching_id("fight")
        async def on_test_button(inter, reset_timeout=False):
            on_click.kill()
            await msg.edit(components=[row])
            return await Attack.attack(self, ctx, inter)

        # @on_click.matching_id("act")
        # async def on_test_button(inter, reset_timeout=False):
        # await msg.edit(components=[])
        # on_click.kill()
        # return await Act.act(self, ctx)

        @on_click.matching_id("items")
        async def on_test_button(inter, reset_timeout=False):
            await msg.edit(components=[row])
            on_click.kill()
            return await Items.use(self, ctx, inter)

        @on_click.matching_id("spare")
        async def on_test_button(inter, reset_timeout=False):
            await msg.edit(components=[row])
            on_click.kill()
            return await Mercy.spare(self, ctx, inter)

        @on_click.timeout
        async def on_timeout():
            row.disable_buttons()
            embed.description = "You took too much to reply!"
            await msg.edit(embed=embed, components=[row])
            data = {
                "selected_monster": None,
                "fighting": None
            }
            return await ctx.bot.players.update_one({"_id": ctx.author.id}, {"$set": data})


class Attack:
    async def attack(self, ctx, inter):
        event = ctx.bot.events
        type_mon = None
        data = ctx.bot.monsters
        author = ctx.author
        info = await ctx.bot.players.find_one({"_id": author.id})
        user_wep = info["weapon"]
        user_ar = info["armor"]
        user_location = info["location"]
        monster = info["selected_monster"]
        if monster == None:
            monster = info["last_monster"]
        lootbag = random.randint(1, 10)
        damage = info["damage"]
        enemy_hp = info["monster_hp"]

        min_dmg = ctx.bot.items[user_wep]["min_dmg"]
        min_dfs = ctx.bot.items[user_ar]["min_dfs"]
        max_dmg = ctx.bot.items[user_wep]["max_dmg"]
        max_dfs = ctx.bot.items[user_ar]["max_dfs"]
        max_health = info["max_health"]
        enemy_min_gold = data[monster]["min_gold"]
        enemy_max_gold = data[monster]["max_gold"]
        enemy_xp_min = data[monster]["min_xp"]
        enemy_xp_max = data[monster]["max_xp"]

        enemy_gold = random.randint(enemy_min_gold, enemy_max_gold)
        enemy_xp = random.randint(enemy_xp_min, enemy_xp_max)
        user_dmg = random.randint(min_dmg, max_dmg)
        user_dfs = random.randint(min_dfs, max_dfs)

        dodge_chance = random.randint(1, 10)

        atem = discord.Embed(title="You Attack")

        if dodge_chance in [5, 9]:
            atem.description = f"**{monster}** Dodged the attack!"
            await inter.reply(ctx.author.mention, embed=atem)
            await asyncio.sleep(3)
            await Attack.counter_attack(self, ctx)
        else:
            # player attack
            damage = int(user_dmg) + int(damage)
            enemy_hp_after = int(enemy_hp) - damage
            enemy_hp_after = max(enemy_hp_after, 0)
            atem.description = f"You Damaged **{monster}**\n**-{user_dmg}HP**\ncurrent monster hp: **{enemy_hp_after}HP**"
            atem.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/793382520665669662/803885802588733460/image0.png"
            )
            await inter.reply(ctx.author.mention, embed=atem)
            if enemy_hp_after <= 0:
                await asyncio.sleep(1)
                embed = discord.Embed(
                    title="You Won!",
                    description=f"You Earned **{int(enemy_gold)} G** and **{int(enemy_xp)}XP**",
                    color=discord.Colour.gold(),
                )
                embed.set_thumbnail(
                    url="https://cdn.discordapp.com/attachments/850983850665836544/878997428840329246/image0.png"
                )
                xp_multi = int(info["multi_xp"])
                gold_multi = int(info["multi_g"])
                gold = enemy_gold
                exp = enemy_xp
                # Multiplier
                if info["multi_g"] > 1 and info["multi_xp"] > 1:
                    gold = gold * info["multi_xp"]
                    exp = exp * info["multi_g"]
                    embed.description += f"\n\n**[MULTIPLIER]**\n> **[{xp_multi}x]** XP: **+{int(exp - enemy_xp)}** ({int(exp)})\n> **[{gold_multi}x]** GOLD: **+{int(gold - enemy_gold)}** ({int(gold)})"
                # Events
                if event is not None:
                    xp_multi = int(event["multi_xp"])
                    gold_multi = int(event["multi_g"])
                    gold = gold * event["multi_xp"]
                    exp = exp * event["multi_g"]
                    name = event["name"]

                    embed.description += f"\n\n**[{name.upper()} EVENT!]**\n> **[{xp_multi}x]** XP: **+{int(exp - enemy_xp)}** ({int(exp)})\n> **[{gold_multi}x]** GOLD: **+{int(gold - enemy_gold)}** ({int(gold)})"

                info["selected_monster"] = None
                info["monster_hp"] = 0
                info["fighting"] = False
                if ctx.invoked_with in ctx.bot.cmd_list:
                    info["rest_block"] = time.time()

                info["gold"] = info["gold"] + gold
                info["exp"] = info["exp"] + exp

                if len(ctx.bot.monsters[monster]["loot"]) > 0:
                    num = random.randint(0, 6)
                    crate = ctx.bot.monsters[monster]["loot"][0]
                    if num < 2:
                        info[crate] += 1
                        embed.description += (
                            f"\n\n**You got a {crate}, check u?crate command**"
                        )
                info["kills"] = info["kills"] + 1
                await ctx.bot.players.update_one({"_id": author.id}, {"$set": info})
                await Core._check_levelup(self, ctx)
                await ctx.send(embed=embed)
                print(f"{ctx.author} has ended the fight")
            else:
                info["monster_hp"] = enemy_hp_after
                await ctx.bot.players.update_one({"_id": author.id}, {"$set": info})
                await asyncio.sleep(2)
                return await Attack.counter_attack(self, ctx)

        return

    async def counter_attack(self, ctx):
        author = ctx.author
        type_mon = None
        data = ctx.bot.monsters

        info = await ctx.bot.players.find_one({"_id": ctx.author.id})
        user_location = info["location"]
        enemy_define = info["selected_monster"]
        if enemy_define == None:
            enemy_define = info["last_monster"]
        enemy_define_hp = info["monster_hp"]
        enemy_dmg = data[enemy_define]["atk"]
        user_ar = info["armor"].lower()
        min_dfs = ctx.bot.items[user_ar]["min_dfs"]
        max_dfs = ctx.bot.items[user_ar]["max_dfs"]
        user_dfs = random.randint(min_dfs, max_dfs)
        user_hp = info["health"]
        user_max_hp = info["max_health"]

        enemy_dmg = enemy_dmg - int(user_dfs)
        if enemy_dmg <= 0:
            enemy_dmg = 1
            enemy_dmg = random.randint(enemy_dmg, enemy_dmg + 10)
        dodge_chance = random.randint(1, 10)
        atem = discord.Embed(title=f"{enemy_define} Attacks")

        if dodge_chance >= 9:
            atem.description = f"**{ctx.author.name}** Dodged the attack!"
            await ctx.send(ctx.author.mention, embed=atem)
            await asyncio.sleep(3)
            return await Menu.menu(self, ctx)

        user_hp_after = int(user_hp) - int(enemy_dmg)
        gold_lost = random.randint(10, 40) + info["level"]
        atem.description = f"**{enemy_define}** Attacks\n**-{enemy_dmg}HP**\ncurrent hp: **{user_hp_after}HP\n{await Core.get_bar(user_hp_after, user_max_hp)}**"
        atem.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/793382520665669662/803885802588733460/image0.png"
        )
        await asyncio.sleep(2)
        await ctx.send(ctx.author.mention, embed=atem)

        if user_hp_after <= 0:
            user_hp_after = 0
            info["gold"] = info["gold"] - gold_lost
            info["gold"] = max(info["gold"], 0)
            info["deaths"] = info["deaths"] + 1
            info["health"] = 10
            info["fighting"] = False
            info["selected_monster"] = None
            info["monster_hp"] = 0
            await ctx.bot.players.update_one({"_id": author.id}, {"$set": info})

            await asyncio.sleep(3)
            femb = discord.Embed(
                title="You Lost <:broken_heart:865088299520753704>",
                description=f"**Stay Determines please!, You lost {gold_lost} G**",
                color=discord.Colour.red(),
            )
            print(f"{ctx.author} has ended the fight")
            await ctx.send(ctx.author.mention, embed=femb)
            return
        else:
            info["health"] = user_hp_after
            await ctx.bot.players.update_one({"_id": author.id}, {"$set": info})
            await asyncio.sleep(3)
            return await Menu.menu(self, ctx)


class Items:
    async def weapon(self, ctx, item):
        data = await ctx.bot.players.find_one({"_id": ctx.author.id})
        data["inventory"].remove(item)
        data["inventory"].append(data["weapon"])
        data["weapon"] = item
        await ctx.bot.players.update_one({"_id": ctx.author.id}, {"$set": data})
        await ctx.send(f"Succesfully equiped {item.title()}")

        return await Attack.counter_attack(self, ctx)

    async def armor(self, ctx, item):
        data = await ctx.bot.players.find_one({"_id": ctx.author.id})
        data["inventory"].remove(item)
        data["inventory"].append(data["armor"])

        data["armor"] = item
        await ctx.bot.players.update_one({"_id": ctx.author.id}, {"$set": data})
        await ctx.send(f"Succesfully equiped {item.title()}")

        return await Attack.counter_attack(self, ctx)

    async def food(self, ctx, item):
        data = await ctx.bot.players.find_one({"_id": ctx.author.id})
        data["inventory"].remove(item)
        heal = ctx.bot.items[item]["HP"]
        data["health"] += heal

        if data["health"] >= data["max_health"]:
            data["health"] = data["max_health"]
            await ctx.bot.players.update_one({"_id": ctx.author.id}, {"$set": data})
            await ctx.send("Your health maxed out")
            return await Attack.counter_attack(self, ctx)
        health = data["health"]
        await ctx.bot.players.update_one({"_id": ctx.author.id}, {"$set": data})
        await ctx.send(
            f"You consumed {item}, restored {heal}HP\n\nCurrent health: {health}HP"
        )
        return await Attack.counter_attack(self, ctx)

    async def use(self, ctx, inter):
        def countoccurrences(store, value):
            try:
                store[value] = store[value] + 1
            except KeyError as e:
                store[value] = 1
                return

        await loader.create_player_info(ctx, ctx.author)
        data = await ctx.bot.players.find_one({"_id": ctx.author.id})
        if len(data["inventory"]) == 0:
            await ctx.send("You have nothing to use")
            return await Attack.counter_attack(self, ctx)

        items_list = []
        for i in data["inventory"]:
            items_list.append(i)

        embed = discord.Embed(
            title="Inventory",
            description="Welcome to your Inventory!",
            color=discord.Colour.random(),
        )

        rows = []
        lista = []
        inventory = []
        store = {}
        for data in data["inventory"]:
            countoccurrences(store, data)
        for k, v in store.items():
            inventory.append({f"{k}": f"{v}x"})
        for item in inventory:
            for key in item:
                lista.append(
                    Button(
                        label=f"{key.title()} {item[key]}",
                        custom_id=key.lower(),
                        style=2,
                    )
                )

        for i in range(0, len(lista), 5):
            rows.append(ActionRow(*lista[i: i + 5]))

        msg = await inter.reply(embed=embed, components=rows)

        on_click = msg.create_click_listener(timeout=120)

        @on_click.not_from_user(ctx.author, cancel_others=True, reset_timeout=False)
        async def on_wrong_user(inter):
            await inter.reply("This is not yours kiddo!", ephemeral=True)

        @on_click.from_user(ctx.author)
        async def selected(inter):
            on_click.kill()
            item = inter.component.id
            await msg.edit(components=[])
            try:
                await getattr(Items, ctx.bot.items[item]["func"])(self, ctx, item)
            except KeyError:
                await ctx.send("Nothing happened")
                await asyncio.sleep(2)
                return await Attack.counter_attack(self, ctx)


"""
class Act:
    async def act(self, ctx):
        type_mon = "monster"
        data = ctx.bot.monsters
        info = await ctx.bot.players.find_one({"_id": ctx.author.id})
        monster = info["selected_monster"]
        if monster == None:
            monster = info["last_monster"]
        location = info["location"]
        enemy_max_dmg = data[info["selected_monster"]]["atk"]
        dg = data[monster]["check_data"]

        embed = discord.Embed(title="Acts, Choose One", description="**Check**")
        await ctx.send(embed=embed)
        res = await ctx.bot.wait_for(
            "message",
            check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
            timeout=120,
        )

        if res.content.lower() == "check":
            embch = discord.Embed(
                title="Monster Stats",
                description=f"**{enemy_max_dmg}DMG, {dg}**",
                color=discord.Colour.teal(),
            )
            await ctx.send(embed=embch)
            await asyncio.sleep(6)
        await asyncio.sleep(3)
        await Attack.counter_attack(self, ctx)
"""


class Mercy:
    async def spare(self, ctx, inter):
        info = await ctx.bot.players.find_one({"_id": ctx.author.id})
        monster = info["selected_monster"]
        if monster == None:
            monster = info["last_monster"]
        if monster == "sans":
            await ctx.send(
                "Get dunked on!!, if were really freinds... **YOU WON'T COME BACK**"
            )
            info["selected_monster"] = None
            info["fighting"] = False
            info["health"] = 10
            if str(ctx.invoked_with) == "fboss":
                info["rest_block"] = time.time()
            await bot.players.update_one({"_id": author.id}, {"$set": info})
            return

        func = ["spared", "NotSpared", "spared"]
        monster = info["selected_monster"]
        sprfunc = random.choice((func))
        embed1 = discord.Embed(
            title="Mercy", description=f"You tried to spare {monster}"
        )
        embed1.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/793382520665669662/803887253927100436/image0.png"
        )
        msg = await inter.reply(embed=embed1)
        await asyncio.sleep(5)
        embed2 = discord.Embed(
            title="Mercy", description="They didn't accepted your mercy"
        )

        embed2.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/793382520665669662/803889297936613416/image0.png"
        )
        embed3 = discord.Embed(title="Mercy", description="They accepted your mercy")
        embed3.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/793382520665669662/803887253927100436/image0.png"
        )
        if sprfunc == "spared":
            if str(ctx.invoked_with) == "fboss":
                info["rest_block"] = time.time()
            info["selected_monster"] = None
            info["fighting"] = False
            print(f"{ctx.author} has ended the fight")
            await msg.edit(embed=embed3)
            await ctx.bot.players.update_one({"_id": ctx.author.id}, {"$set": info})
        elif sprfunc == "NotSpared":
            await msg.edit(embed=embed2)

            await asyncio.sleep(4)
            await Attack.counter_attack(self, ctx)  # replace