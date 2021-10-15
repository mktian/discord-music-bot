import discord
from discord.ext import commands

from youtube_dl import YoutubeDL
import datetime
import validators
from urllib.parse import urlparse, parse_qs

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = False

        self.music_queue = []
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}

        self.vc = ""

    def search_yt(self, item):
        YDL_OPTIONS = {'format': 'bestaudio/best', 'no-playlist': 'False'}
        
        with YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                yt_list = []

                if validators.url(item):
                    if "playlist?list" in item:
                        url = parse_qs(urlparse(item).query)["list"][0]
                    else:
                        item = parse_qs(urlparse(item).query)["v"][0]
                        url = "ytsearch:%s" % item
                else:        
                    url = "ytsearch:%s" % item

                info = ydl.extract_info(url, download=False)['entries']

                for i in info:
                    yt_list.append(
                        {'source': i['formats'][0]['url'], 'title': i['title'], 'link_url': i['webpage_url'],
                         'thumbnail_url': i['thumbnails'][0]['url'], 'duration': i['duration']})
                    
                print(yt_list)
                
            except:
                raise
                # return []

        return yt_list

    def play_next(self):
        # removes the played song
        self.music_queue.pop(0) 
        
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0]['source']

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    # infinite loop checking 
    async def play_music(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0]['source']

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    @commands.command(name="play", help="Plays a selected song from youtube", aliases=['p'])
    async def p(self, ctx, *args):
        query = " ".join(args)
        
        if ctx.author.voice == None:
            # you need to be connected so that the bot knows where to go
            embed = discord.Embed(
                description='Are you crazy? You need to connect to a voice channel first.'
            )
            await ctx.send(embed=embed)
            # await ctx.send("Are you crazy? You need to connect to a voice channel first.")
            return
        
        if query.isupper():
            embed = discord.Embed(
                description='Why you shouting? No. Shouting at me no good man.'
            )
            await ctx.send(embed=embed)
            # await ctx.send('Why you shouting? No. Shouting at me no good man.')
            return
    
        voice_channel = ctx.author.voice.channel
        songs = self.search_yt(query)
        if len(songs) < 1:
            embed = discord.Embed(
                description='You search like lady eh? I went to the hill and went down and couldn\'t find your video. Benchode.'
            )
            await ctx.send(embed=embed)
        elif len(songs) == 1:
            song = songs[0]
            embed = discord.Embed(
                title='Song added to queue:',
                description='[{t}]({u}) - {d}'.format(t=song['title'], u=song['link_url'],
                                                        d=str(datetime.timedelta(seconds=song['duration']))),
            )
            embed.set_thumbnail(url=song['thumbnail_url'])
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title='Playlist added to queue:',
                description='[{t}]({u}) - {d} Songs'.format(t=query, u=query, d=len(songs)),
            )
            embed.set_thumbnail(url=songs[0]['thumbnail_url'])
            await ctx.send(embed=embed)

            # await ctx.send("{} added to the queue".format(song['title']))
            
        self.music_queue.extend(songs)
        
        # try to connect to voice channel if you are not already connected
        if self.vc == "" or not self.vc.is_connected() or self.vc is None:
            self.vc = await voice_channel.connect()

        if not self.is_playing:
            await self.play_music()

    @commands.command(name="queue", help="Displays the current songs in queue", aliases=['q'])
    async def q(self, ctx):
        retval = ""
        for i in range(0, min(len(self.music_queue),10)):
            s = self.music_queue[i]
            retval += '{i}: \t [{t}]({u}) - {d}'.format(i=i + 1, t=s['title'], u=s['link_url'],
                                                        d=str(datetime.timedelta(seconds=s['duration']))) + "\n"
        if retval != "":
            embed = discord.Embed(
                title='Current songs in queue:',
                description=retval
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title='Current songs in queue:',
                description='Bloody NO! There are no bloody songs in the queue, benchode.'
            )
            await ctx.send(embed=embed)

    @commands.command(name="skip", help="Skips the current song being played", aliases=['sk','next'])
    async def skip(self, ctx):
        if len(self.music_queue) < 1:
            embed = discord.Embed(
                description='There are no songs in the queue, bloody.'
            )
            await ctx.send(embed=embed)
            # await ctx.send('There are no songs in the queue, bloody.')
        else:
            self.vc.stop()
            if len(self.music_queue) > 1:
                song = self.music_queue[1]
                embed = discord.Embed(
                    title='Now Playing:',
                    description='[{t}]({u}) - {d}'.format(t=song['title'], u=song['link_url'],
                                                        d=str(datetime.timedelta(seconds=song['duration']))),
                )
                embed.set_thumbnail(url=song['thumbnail_url'])
            else:
                embed = discord.Embed(
                    description='There are no more songs in the queue, bloody.'
                )
                await ctx.send(embed=embed)
                # await ctx.send('There are no more songs in the queue, bloody.')
            await ctx.send(embed=embed)

    @commands.command(name="stop", help="Stops and clears queue", aliases=['end'])
    async def stop(self, ctx):
        # if len(self.music_queue) < 1:
        #     await ctx.send('Nothing\'s playing Sammy.')
        # else:
        self.vc.stop()
        self.music_queue = []
        embed = discord.Embed(
            description='Okay, have a nice day.'
        )
        await ctx.send(embed=embed)
        await self.vc.disconnect()
        self.is_playing = False

    @commands.command(name="now", help="Current song information", aliases=['np'])
    async def now(self, ctx):
        if len(self.music_queue) < 1:
            embed = discord.Embed(
                description='Nothing\'s even playing right now. YOU BLUNDER!'
            )
            await ctx.send(embed=embed)
            # await ctx.send('Nothing\'s even playing right now. YOU BLUNDER!')
        else:
            song = self.music_queue[0]
            embed = discord.Embed(
                title='Now Playing:',
                description='[{t}]({u}) - {d}'.format(t=song['title'], u=song['link_url'],
                                                      d=str(datetime.timedelta(seconds=song['duration']))),
            )
            embed.set_thumbnail(url=song['thumbnail_url'])
            await ctx.send(embed=embed)

    @commands.command(name="remove", help="Remove song from queue", aliases=['rm'])
    async def remove(self, ctx, index: int):
        if not index or index == '' or type(index) != int:
            embed = discord.Embed(
                description='You BLUNDER! What am I supposed to remove? You benchode.'
            )
            return await ctx.send(embed=embed)
        elif index > len(self.music_queue) or index < 1:
            embed = discord.Embed(
                description='You BLUNDER! You think you\'re a smart guy eh? I can\'t remove something that doesn\'t exist, benchode.'
            )
            await ctx.send(embed=embed)
        elif len(self.music_queue) < 1:
            embed = discord.Embed(
                description='Are you crazy? There are no songs in the queue, bloody.'
            )
            await ctx.send(embed=embed)
        elif len(self.music_queue) == 1:
            embed = discord.Embed(
                description='If you want to go then you use -stop next time and then go down.'
            )
            await ctx.send(embed=embed)
        else:
            index -= 1
            removed = self.music_queue[index]
            self.music_queue.pop(index)
            
            embed = discord.Embed(
                title='Removed from queue:',
                description='[{t}]({u}) - {d}'.format(t=removed['title'], u=removed['link_url'],
                                                      d=str(datetime.timedelta(seconds=removed['duration']))),
            )
            embed.set_thumbnail(url=removed['thumbnail_url'])
            await ctx.send(embed=embed)

    @commands.command(name="skipto", help="Skips to song # and remove everything before it", aliases=['st'])
    async def skipto(self, ctx, index: int):
        if not index or index == '' or type(index) != int:
            embed = discord.Embed(
                description='You BLUNDER! What am I supposed to remove? You benchode.'
            )
            return await ctx.send(embed=embed)
        elif index > len(self.music_queue) or index < 1:
            embed = discord.Embed(
                description='You BLUNDER! You think you\'re a smart guy eh? I can\'t remove something that doesn\'t exist, benchode.'
            )
            await ctx.send(embed=embed)
        elif len(self.music_queue) < 1:
            embed = discord.Embed(
                description='Are you crazy? There are no songs in the queue, bloody.'
            )
            await ctx.send(embed=embed)
        elif len(self.music_queue) == 1:
            embed = discord.Embed(
                description='If you want to go then you use -stop next time and then go down.'
            )
            await ctx.send(embed=embed)
        else:
            index -= 1
            self.music_queue = self.music_queue[index:]
            song = self.music_queue[0]
            
            embed = discord.Embed(
                title='Now Playing:',
                description='[{t}]({u}) - {d}'.format(t=song['title'], u=song['link_url'],
                                                      d=str(datetime.timedelta(seconds=song['duration']))),
            )
            embed.set_thumbnail(url=song['thumbnail_url'])
            await ctx.send(embed=embed)
            
    @commands.command(name="feedback", help="Send feedback about Benjamin to welcoming ears")
    async def feedback(self, ctx, txt):
        if not txt or txt == '':
            embed = discord.Embed(
                description='Why you whisper eh? Ben cannot hear you innit?'
            )
            return await ctx.send(embed=embed)
        else:            
            embed = discord.Embed(
                description='BLOODY NO!'
            )
            await ctx.send(embed=embed)