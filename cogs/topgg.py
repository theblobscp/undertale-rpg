import time

import dbl
from discord.ext import commands


class TopGG(commands.Cog):
    """
    This example uses dblpy's webhook system.
    In order to run the webhook, at least webhook_port must be specified (number between 1024 and 49151).
    """

    def __init__(self, bot):
        self.bot = bot
        self.bot.topggpy = dbl.DBLClient(
            self.bot,
            self.bot.TopGGToken,
            webhook_path="/dblwebhook",
            webhook_auth="dady2005",
            webhook_port=55111,
        )

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        vote_data = data
        voter = await self.bot.fetch_user(vote_data["user"])
        info = await self.bot.players.find_one({"_id": voter.id})
        if info is None:
            print("{bcolors.WARNING} This user is not registered.")
            return
        info["gold"] = info["gold"] + 500
        info["standard crate"] += 1
        info["last_voted"] = time.time()
        await self.bot.players.update_one({"_id": voter.id}, {"$set": info})
        print(f"Received a vote from {str(voter)}, They got their rewards succesfully")

    @commands.Cog.listener()
    async def on_dbl_test(self, data):
        vote_data = data
        voter = await self.bot.fetch_user(vote_data["user"])
        info = await self.bot.players.find_one({"_id": voter.id})
        info["gold"] = info["gold"] + 500
        info["standard crate"] += 1
        await self.bot.players.update_one({"_id": voter.id}, {"$set": info})
        print(f"Received a vote from {str(voter)}, They got their rewards succesfully")

    @commands.command()
    @commands.is_owner()
    async def close(self, ctx):
        await self.bot.topggpy.close()
        await ctx.reply("closed the webhook")


def setup(bot):
    bot.add_cog(TopGG(bot))