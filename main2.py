import discord
import draft
import helpers

client = discord.Client()
messagableUsers = {}
nailChanID = 806068830702534677
nailDraftChannelID = 806095749938413598
nailMiscChannelID = 806095765776367658
amateurNailChanID = 806068830702534677
amateurNailDraftChannelID = 806095749938413598
amateurNailMiscChannelID = 806095765776367658
nailChanIDsToChannelIDs = {nailChanID: (nailDraftChannelID, nailMiscChannelID),
                           amateurNailChanID: (amateurNailDraftChannelID, amateurNailMiscChannelID)}
botChannelIDs = [nailDraftChannelID, amateurNailDraftChannelID]    # the first 2
# are wcc discord map and draft channels


@client.event
async def on_ready():
    print(str(client.user) + " is online.")


@client.event
async def on_message(message):
    if message.author == client.user: return  # break if the message is our own message; these should be ignored
    if await tryStartNAILDraft(message, message.author):
        return
    if (message.channel.id in botChannelIDs) or isinstance(message.channel, discord.DMChannel):
        user = getMessagableUser(message.author)
        await parse(message.content, user)
        if not isinstance(message.channel, discord.DMChannel):
            await message.delete()


async def parse(messageStr, user):
    messageStr = messageStr.lower()
    command = messageStr.split()[0]
    #print(messageStr)
    if command[0] == "!":
        command = command[1:]
    else:
        return
    arg = messageStr[len(command) + 1:];arg = arg.strip()

    if command in draft.asyncCommands:
        await draft.asyncCommands[command](arg, user)
    elif command in draft.asyncCommandsClientArg:
        await draft.asyncCommandsClientArg[command](arg, user, client)
    else:
        await user.send("Command not found, try !info for a list of commands")
    # break the message into first word, then everything after the first space is a second block


def getMessagableUser(user):
    if user.id not in messagableUsers:
        messagableUsers[user.id] = helpers.MessagableUser(user)
    return messagableUsers[user.id]


async def tryStartNAILDraft(msg, user):
    if user.id in nailChanIDsToChannelIDs:
        channels = nailChanIDsToChannelIDs[user.id]
        if msg.channel.id == channels[0]:
            command = msg.content.lower().split(",")
            matchID = command[0]
            captainOne = getMessagableUser(client.get_user(int(command[1])))
            captainTwo = getMessagableUser(client.get_user(int(command[2])))
            pickBanOrder = command[3]
            await draft.startDraft(pickBanOrder, captainOne, client, "char", captainTwo, matchID, channels)
            await msg.delete()
            return True
    return False

TOKEN = open('token2.secret', 'r').read()

client.run(TOKEN)
