import random
import discord
import helpers

useGlobalBans = False

activeDrafts = []
draftsByJoinCode = {}

champList = [  # thanks deniz
    "alysia", "ashka", "bakko", "blossom", "croak", "destiny", "ezmo", "freya",
    "iva", "jade", "jamila", "jumong", "lucie", "oldur", "pearl", "pestilus",
    "poloma", "raigon", "rook", "ruh kaan", "shen rao", "shifu", "sirius",
    "taya", "thorn", "ulric", "varesh", "zander",
]
champAlias = {"blos": "blossom", "pest": "pestilus", "dio": "pearl",
    "ruh": "ruh kaan", "rk": "ruh kaan", "shen": "shen rao",
    "luke": "freya", "dest": "destiny", "pol": "poloma",
    "lucy": "lucie", "jam": "jamila", "jum": "jumong",
    "var": "varesh", "uni": "jumong", "frog": "croak",
    "polo": "poloma", "catchy": "thorn", "tomiy": "rook",
    "LDK": "bakko", "chisaku": "jade", "peon": "poloma",
    "averse": "taya", "arkdn": "rook", "mGalante": "rook",
    "egirl": "ulric", "lokrium": "poloma"
}
mapList = [
    "mount araz day", "mount araz night", "orman temple day", "orman temple night",
    "sky ring day", "sky ring night", "blackstone arena day", "blackstone arena night",
    "dragon garden day", "dragon garden night", "daharin battlegrounds day", "daharin battlegrounds night",
    "misty woods day", "misty woods night", "meriko summit day", "meriko summit night",
    "the great market day", "the great market night"
]
bannedMaps = ["sky ring day", "orman temple day", "misty woods day", "misty woods night", "meriko summit day"]
defaultMapList = [_map for _map in mapList if _map not in bannedMaps]
dioMapList = ["mount araz night", "dragon garden night", "meriko summit night", "the great market night",
              "blackstone arena day", "daharin battlegrounds night", "orman temple night"]
mapAlias = {"araz day": "mount araz day", "araz d": "mount araz day",
            "araz night": "mount araz night", "araz n": "mount araz night",
            "orman day": "orman temple day", "orman d": "orman temple day",
            "orman night": "orman temple night", "orman n": "orman temple night",
            "sky day": "sky ring day", "sky d": "sky ring day",
            "sky night": "sky ring night", "sky n": "sky ring night",
            "black day": "blackstone arena day", "black d": "blackstone arena day",
            "black night": "blackstone arena night", "black n": "blackstone arena night",
            "dragon day": "dragon garden day", "dragon d": "dragon garden day",
            "dragon night": "dragon garden night", "dragon n": "dragon garden night",
            "daharin day": "daharin battlegrounds day", "daharin d": "daharin battlegrounds day",
            "daharin night": "daharin battlegrounds night", "daharin n": "daharin battlegrounds night",
            "misty day": "misty woods day", "misty d": "misty woods day",
            "misty night": "misty woods night", "misty n": "misty woods night",
            "meriko day": "meriko summit day", "meriko d": "meriko summit day",
            "meriko night": "meriko summit night", "meriko n": "meriko summit night",
            "great market day": "the great market day", "great market d": "the great market day",
            "market day": "the great market day", "market d": "the great market day",
            "great market night": "the great market night", "great market n": "the great market night",
            "market night": "the great market night", "market n": "the great market night",
            }


async def version(arg, user):
    await user.send("Version 1.04")


async def startDraft(arg, user, client, draftType, captainTwo=None, id=None, channels=None):
    if await alreadyInDraft(user):
        return
    if draftType == "char":
        if arg == "nail":
            order = ["ban", "ban", "pick", "pick", "ban", "pick"]
        elif arg == "":
            order = ["ban", "ban", "pick", "pick", "ban", "pick"]
        else:
            order = await makeOrder(arg, user)
            if order is None:
                return
    if draftType == "map":
        rand = True
        if arg == "all":
            pool = mapList
        if arg == "default":
            pool = defaultMapList
        else:
            pool = dioMapList; rand = False

    newDraft = CharacterDraft(user, channels, id, order) if draftType == "char" else MapDraft(user, channels, id, pool, rand)
    activeDrafts.append(newDraft)
    draftsByJoinCode[newDraft.joinCode] = newDraft
    await newDraft.asyncInit(client, captainTwo)


async def makeOrder(arg, user):
    _map = {"p": "pick", "b": "ban"}
    order = []
    num_picks = 0
    for char in arg:
        if char in _map:
            if char == "p": num_picks += 1
            if num_picks > 3:
                await user.send("Invalid argument for character draft creation: too many picks (max 3)")
                return
            if num_picks == 3 and char == "b":
                await user.send("Invalid argument for character draft creation: ban after final pick.")
                return
            order.append(_map[char])
        else:
            await user.send("Invalid argument for character draft creation: invalid character in argument (all characters must be p or b)")
            return
    return order


async def startCharacterDraft(arg, user, client):
    await startDraft(arg, user, client, "char")


async def startMapDraft(arg, user, client):
    await startDraft(arg, user, client, "map")


async def join(arg, user):
    if await alreadyInDraft(user):
        return
    if arg in draftsByJoinCode:
        await draftsByJoinCode[arg].setCaptainTwo(user)
    else:
        await user.send("Draft with code " + str(arg) + " not found.")


async def alreadyInDraft(user):
    for draft in activeDrafts:
        for captain in draft.captains:
            if captain.user == user:
                await user.send("You can't join or create a draft while already in one; type !exit to exit your current draft.")
                return True
    return False


# finds captain and draft that a given user is part of or None if user is not part of a draft
async def findCaptainAndDraft(user):
    for draft in activeDrafts:
        for captain in draft.captains:
            if user == captain.user:
                return captain, draft
    else:
        await user.send("You are not currently part of a draft; try creating a draft with !draft")
        return None, None


async def pick(arg, author):
    captain, draft = await findCaptainAndDraft(author)
    if draft is not None:
        if draft.captainTwo is not None:
            await draft.pick(arg, captain)
        else:
            await author.send("Please wait for the other captain to join the draft before picking or banning.\n"
                              "The join code for your draft is !join " + str(draft.joinCode))


async def ban(arg, author):
    captain, draft = await findCaptainAndDraft(author)
    if draft is not None:
        if draft.captainTwo is not None:
            await draft.ban(arg, captain)
        else:
            await author.send("Please wait for the other captain to join the draft before picking or banning.\n"
                              "The join code for your draft is !join " + str(draft.joinCode))


async def exitDraft(arg, author):
    captain, draft = await findCaptainAndDraft(author)
    if draft is not None:
        await draft.exit(captain)


async def info(arg, author):
    await author.send("**!draft** *or* **!d** `order` to start a character draft\n"
                      "The `order` argument can be left off to start a normal draft\n"
                      "with `pbpbbp` order, or set to `nail` to start a draft with `bppbp` order\n"
                      "or set to an arbitrary order by typing the pick ban order directly, e.g, `pbpp`\n"
                      "**!mapdraft** *or* **!draftmap** *or* **!dm** *or* **!md** to start a map draft\n"
                      "mapdraft can be sent with the argument `all` to include all maps\n"
                      "(e.g, not automatically removing sky day, orman day, meriko day, and both mistys)\n"
                      "**!join** *or* **!j** `code` to join a draft\n"
                      "**!exit** to cancel a draft\n"
                      "**!pick** *or* **!p** `character` or `map` to pick\n"
                      "**!ban** *or* **!b** `character` or `map` to ban\n"
                      "**!info** *or* **!help** is this command\n"
                      "*tip*: you can type `!b orman n` instead of `!ban orman temple night`\n"
                      "every map has one or more shortenings, and characters have some shortenings as well.")



# asyncInit must be called immediately after construction; constructors can't be async for some silly reason
class Draft:
    @property
    def captains(self):
        if self.captainTwo is not None:
            return self.captainOne, self.captainTwo
        else:
            return [self.captainOne]

    def otherCaptain(self, captain):
        if self.captainOne == captain:
            return self.captainTwo
        else:
            return self.captainOne

    def __init__(self, captainOne, channels, draftID=None):
        self.id = draftID
        self.draftChannel = channels[0]   # must be overridden in subclass or messageCaptainDraftTable will break
        self.miscChannel = channels[1]    # 737652559883534406    # pepega hardcoded channel values
        self.captainOne = Captain(captainOne)
        self.captainTwo = None
        while True:
            self.joinCode = str(random.randint(100, 999))  # its just a string, no conversion to or from int
            if self.joinCode not in draftsByJoinCode:
                break
        self.msgsToDeleteAtCleanup = []
        self.msgsToDeleteSoon = []    # deleted after phase advances

    async def asyncInit(self, client, captainTwo=None):
        self.draftChannel = client.get_channel(self.draftChannel)
        self.miscChannel = client.get_channel(self.miscChannel)
        if captainTwo is not None:
            await self.setCaptainTwo(captainTwo)
        else:
            await self.captainOne.user.send(f"Send this code to the other captain:\n`!join {str(self.joinCode)}`")

    async def setCaptainTwo(self, captainTwo):
        if self.captainOne.user == captainTwo:
            await captainTwo.send("You can't join a draft you started.") #commented out for testing purposes, uncomment later
        else:
            self.captainTwo = Captain(captainTwo)
            del draftsByJoinCode[self.joinCode]
            await self.startDraft()

    async def startDraft(self):
        pass

    async def exit(self, captain):
        await self.deleteSoonMessages()
        await captain.user.send("Exiting draft!", None)
        otherCaptain = self.otherCaptain(captain)
        if otherCaptain is not None:
            await self.otherCaptain(captain).user.send("The other captain canceled the draft!", None)
        await self.finishDraft()

    async def deleteSoonMessages(self):
        for captain in self.captains:
            await captain.user.delete()
        await helpers.deleteMessages(self.msgsToDeleteSoon)

    async def finishDraft(self):
        # clean up draft here
        await helpers.deleteMessages(self.msgsToDeleteAtCleanup)
        activeDrafts.remove(self)
        print(str(draftsByJoinCode))
        print(str(self))
        if self.joinCode in draftsByJoinCode:
            print("removed self from draftsbyJoinCode")
            print("before " + str(draftsByJoinCode))
            del draftsByJoinCode[self.joinCode]
            print("after " + str(draftsByJoinCode))
        return

    async def messageCaptainsDraftTable(self, captainOneHeader="", captainTwoHeader="", final=False):
        await self.deleteSoonMessages()
        captainTwoHeader = captainOneHeader if captainTwoHeader == "" else captainTwoHeader
        await helpers.deleteMessages(self.msgsToDeleteSoon)
        for captain in self.captains:
            embed = self.createDraftMessage(captain, self.otherCaptain(captain))
            header = captainOneHeader if captain == self.captainOne else captainTwoHeader
            if not final:
                await captain.user.send(header, "command", embed=embed)
            else:
                await captain.user.send(header, None, embed=embed)
        embedChannel = self.createDraftMessage(self.captainOne, self.captainTwo, True, True)
        channelMsg = await self.draftChannel.send(None, embed=embedChannel)
        if not final:
            self.msgsToDeleteSoon.append(channelMsg)

    def createDraftMessage(self, lclCOne, lclCTwo, nameBothCaptains=False, includeIDFooter=False):  # subclasses must implement
        pass                                                                          # using the helper functions below

    def draftMsgIter(self, totalPB, lcls, listType, fieldOneValue, field2And3Values):
        for i in range(totalPB):
            fieldOneValue += "\n"
            for n, lclCaptain in enumerate(lcls):
                localList = None
                if listType == "picks": localList = lclCaptain.picks
                if listType == "bans": localList = lclCaptain.bans
                if listType == "globalBans": localList = lclCaptain.globalBans  # there has to be a better way todo this

                if len(localList) > i:
                    field2And3Values[n] += helpers.fullCapitalize(localList[i]) + "\n"
                else:
                    field2And3Values[n] += "-----\n"
        return fieldOneValue, field2And3Values

    def draftMsgNames(self, embed, lcls, fieldOneValue, field2And3Values, nameBothCaptains=False):
        if nameBothCaptains:
            captainOneName = lcls[0].user.user.name
        else:
            captainOneName = "You   "
        embed.add_field(name="Captains", value=fieldOneValue)
        embed.add_field(name="**" + captainOneName + "**", value=field2And3Values[0])
        embed.add_field(name="**" + lcls[1].user.user.name + "**", value=field2And3Values[1])


class CharacterDraft(Draft):

    def __init__(self, captainOne, channels, draftID, order):
        channels = (751593893824299049, 737652559883534406) if channels is None else channels
        super().__init__(captainOne, channels, draftID)
        self.index = 0
        if useGlobalBans: self.captainOne.globalBans = self.getGlobalBan(self.captainOne.user.user)
        self.globalBans = []; self.globalBans += self.captainOne.globalBans
        self.order = order

    def getGlobalBan(self, user):
        file = open("global_bans.txt")
        banDict = {}
        for line in file.readlines():
            splitLine = line.lower().split()
            _id = int(splitLine[0])
            _ban = splitLine[1]
            banDict[_id] = _ban
        file.close()
        if user.id in banDict:
            ban = banDict[user.id]
            ban = champAlias[ban] if ban in champAlias else ban
            return [ban]
        else: return []

    async def startDraft(self):
        if useGlobalBans: self.captainTwo.globalBans = self.getGlobalBan(self.captainTwo.user.user)
        self.globalBans += self.captainTwo.globalBans
        draftOrderMsg = "The draft order is: ```ml\n"
        _map = {"pick": "\"pick\" ", "ban": "\'ban\' "}
        for pb in self.order:
            draftOrderMsg += _map[pb]
        draftOrderMsg = draftOrderMsg[:-1]
        draftOrderMsg += "```\n"
        pb = self.order[self.index]
        for captain in self.captains:
            self.msgsToDeleteAtCleanup.append(await captain.user.send(draftOrderMsg, None))
        pbMsg = "**" + pb.capitalize() + "** phase, type !" + pb + " to " + pb + " a champion."
        await self.messageCaptainsDraftTable(pbMsg)

    async def validateChampion(self, arg, captain):
        larg = arg.lower()
        if larg in champAlias:
            larg = champAlias[larg]
        if larg not in champList:
            await captain.user.send("Invalid Champion")
            return None
        return larg

    async def vChampPicks(self, champ, captain):
        champ = await self.validateChampion(champ, captain)
        if champ in self.otherCaptain(captain).bans:
            await captain.user.send("That champion has already been banned by the enemy team")
            return None
        if champ in captain.picks:
            await captain.user.send("You've already picked that champion")
            return None
        if champ in self.globalBans and useGlobalBans:
            await captain.user.send("That champion is globally banned for this draft.")
            return None
        return champ

    async def vChampBans(self, champ, captain):
        champ = await self.validateChampion(champ, captain)
        if champ in captain.bans:
            await captain.user.send("You've already banned that champion")
            return None
        if champ in self.otherCaptain(captain).picks:
            await captain.user.send("That champion has already been picked by the enemy team")
            return None
        if champ in self.globalBans and useGlobalBans:
            await captain.user.send("That champion is already globally banned for this draft.")
            return None
        return champ

    async def pick(self, arg, captain):
        if self.order[self.index] != "pick":
            await captain.user.send("This is a banning phase; please type !ban to ban a champion,"
                                    " or !exit to exit the draft.")
        else:
            champ = await self.vChampPicks(arg, captain)
            if champ is None:
                return

            async def x(string):
                await captain.user.delete()
                await captain.user.send(string, embed=self.createDraftMessage(captain, self.otherCaptain(captain)),
                                        deletionInterval="command")

            if not captain.hasPBThisPhase:
                captain.picks.append(champ)
                captain.hasPBThisPhase = True
                if not await self.tryAdvance():
                    await x("Picked " + helpers.fullCapitalize(champ) + "!")
            else:
                captain.picks[-1] = champ
                await x("Changed pick to " + helpers.fullCapitalize(champ) + "!")

    async def ban(self, arg, captain):
        if self.order[self.index] != "ban":
            await captain.user.send("This is a picking phase; please type !pick to pick a champion,"
                                    " or !exit to exit the draft.")
        else:
            champ = await self.vChampBans(arg, captain)
            if champ is None:
                return

            async def x(string):
                await captain.user.delete()
                await captain.user.send(string, embed=self.createDraftMessage(captain, self.otherCaptain(captain)),
                                        deletionInterval="command")

            if not captain.hasPBThisPhase:
                captain.bans.append(champ)
                captain.hasPBThisPhase = True
                if not await self.tryAdvance():
                    await x("Banned " + helpers.fullCapitalize(champ) + "!")
            else:
                captain.bans[-1] = champ
                await x("Changed ban to " + helpers.fullCapitalize(champ) + "!")

    async def tryAdvance(self):
        if len(self.captainOne.picks) == len(self.captainTwo.picks) and len(self.captainOne.bans) == len(self.captainTwo.bans):
            self.index += 1
            for captain in self.captains: captain.hasPBThisPhase = False
            if self.index >= len(self.order):
                await self.messageCaptainsDraftTable("Draft finished!", final=True)
                await self.finishDraft()
            else:
                pb = self.order[self.index]
                await self.messageCaptainsDraftTable("**" + pb.capitalize() + "** phase, type !" + pb
                                                     + " to " + pb + " a champion.")
            return True
        return False

    def createDraftMessage(self, lclCOne, lclCTwo, nameBothCaptains=False, includeIDFooter=False):
        embed = discord.Embed(color=discord.Colour.from_rgb(122, 27, 68))
        lcls = (lclCOne, lclCTwo)
        totalPicks = 0
        totalBans = 0
        fieldOneValue = ""
        field2And3Values = ["", ""]
        for pb in self.order:
            if pb == "pick":
                totalPicks += 1
            if pb == "ban":
                totalBans += 1

        if useGlobalBans and len(self.globalBans) > 0:
            fieldOneValue += "Global Bans\n"
            totalGlobalBans = max(len(self.captainOne.globalBans), len(self.captainTwo.globalBans))
            fieldOneValue, field2And3Values = self.draftMsgIter(totalGlobalBans, lcls, "globalBans", fieldOneValue, field2And3Values)
            field2And3Values[0] += "\n"; field2And3Values[1] += "\n"

        fieldOneValue += "Picks\n"
        fieldOneValue, field2And3Values = self.draftMsgIter(totalPicks, lcls, "picks", fieldOneValue, field2And3Values)
        field2And3Values[0] += "\n"; field2And3Values[1] += "\n"

        fieldOneValue += "Bans\n"
        fieldOneValue, field2And3Values = self.draftMsgIter(totalBans, lcls, "bans", fieldOneValue, field2And3Values)

        self.draftMsgNames(embed, lcls, fieldOneValue, field2And3Values, nameBothCaptains)
        if self.id is not None and includeIDFooter:
            embed.set_footer(text="Match ID " + str(self.id))
        return embed

    async def finishDraft(self):
        if self.id is not None:
            await self.reportDraftToNailChan()
        await super().finishDraft()

    async def reportDraftToNailChan(self):
        output = ""
        x = lambda k: str(k).lower() + ","
        output += x(self.id)
        bans = []; picks = []
        for captain in self.captains:
            bans += captain.bans
            picks += captain.picks
        for _ban in bans: output += x(_ban)
        for _pick in picks: output += x(_pick)

        await self.miscChannel.send(output[:-1])     # this should be fine since asyncInit is always called after init


class MapDraft(Draft):
    def __init__(self, captainOne, channels, draftID, mapPool, randomStart=True):
        channels = (753698814526750720, 737652559883534406) if channels is None else channels
        super().__init__(captainOne, channels, draftID)
        if randomStart:
            self.currentCaptain = random.choice(self.captains)
        else:
            self.currentCaptain = self.captainOne
        self.mapPool = mapPool
        self.totalMaps = 0

    async def startDraft(self):
        msg = "Captains will take turns banning maps until one is left, starting with **" + self.currentCaptain.user.user.name + "**."
        for captain in self.captains:
            await captain.user.send(msg, "command")
        await self.sendCaptainsDraftTableMapDraftWrapper()

    async def pick(self, arg, captain):
        await captain.user.send("Picking is not currently part of how map drafting works.")

    # returns a valid map or None if the map ban was invalid
    async def vMapBan(self, arg, captain):
        pMap = arg.lower()    # pMap = possible map
        if pMap in mapAlias:
            pMap = mapAlias[pMap]
        if pMap not in self.mapPool:
            await captain.user.send("Map not found; for a list of maps try !mapinfo")
            return None
        if pMap in captain.bans:
            await captain.user.send("You've already banned this map.")
            return None
        if pMap in self.otherCaptain(captain).bans:
            await captain.user.send("The enemy captain has already banned this map.")
            return None
        return pMap

    async def ban(self, arg, captain):
        # check if captain the currently active captain
        if captain != self.currentCaptain:
            await captain.user.send("You are not the currently active captain; "
                                    "please wait for the other captain to ban a map.")
            return
        # check if ban is valid
        brMap = await self.vMapBan(arg, captain)
        if brMap is None:
            return
        captain.bans.append(brMap)
        await captain.user.send("Banned " + helpers.fullCapitalize(brMap) + "!")
        await self.advance()

    async def advance(self):
        self.currentCaptain = self.otherCaptain(self.currentCaptain)
        final = len(self.remainingMaps) <= 1
        await self.sendCaptainsDraftTableMapDraftWrapper(final)
        if final: await self.finishDraft()

    async def sendCaptainsDraftTableMapDraftWrapper(self, final=False):    # do i get an award for long bad names
        headers = []
        for captain in self.captains:
            if captain == self.currentCaptain:
                headers.append("Type !ban to **Ban** a map:")
            else:
                headers.append("Please wait for the other captain to ban a map.")
        await self.messageCaptainsDraftTable(headers[0], headers[1], final)

    def createDraftMessage(self, lclCOne, lclCTwo, nameBothCaptains=False, includeIDFooter=False):
        embed = discord.Embed(color=discord.Colour.from_rgb(122, 27, 68))
        lcls = (lclCOne, lclCTwo)
        remMaps = self.remainingMaps

        field1Value = "Bans\n"
        field2And3Values = ["", ""]

        field1Value, field2And3Values = self.draftMsgIter(int(self.totalMaps/2), lcls, "bans", field1Value, field2And3Values)
        self.draftMsgNames(embed, lcls, field1Value, field2And3Values, nameBothCaptains)

        bottomFieldName = "Remaining Maps" if len(remMaps) > 1 else "Chosen Map"
        remainingMapsString = ""
        for _map in remMaps:
            if len(remainingMapsString) > 35:
                if len(remainingMapsString.splitlines()[-1]) > 35:
                    remainingMapsString += "\n"
            remainingMapsString += helpers.fullCapitalize(_map) + ", "
        if len(remMaps) == 1: remainingMapsString = remainingMapsString[:-2]
        embed.add_field(name=bottomFieldName, value=remainingMapsString, inline=False)
        if self.id is not None and includeIDFooter:
            embed.set_footer(text="Match ID " + str(self.id))
        return embed

    @property
    def remainingMaps(self):
        _bannedMaps = self.captainOne.bans + self.captainTwo.bans
        _remainingMaps = []
        for _map in self.mapPool:
            if _map not in _bannedMaps:
                _remainingMaps.append(_map)
        return _remainingMaps


class Captain:
    def __init__(self, user):
        self.user = user
        self.picks = []
        self.bans = []
        self.globalBans = []
        self.hasPBThisPhase = False


asyncCommands = {"join": join, "j": join, "pick": pick, "p": pick, "ban": ban, "b": ban,
                 "exit": exitDraft, "info": info, "help": info, "ver": version, "version": version}

asyncCommandsClientArg = {
                 "draft": startCharacterDraft, "d": startCharacterDraft,
                 "mapdraft": startMapDraft, "draft map": startMapDraft, "md": startMapDraft, "map draft": startMapDraft,
                 "draftmap": startMapDraft, "dm": startMapDraft
}
