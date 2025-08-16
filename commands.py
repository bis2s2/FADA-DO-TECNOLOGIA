
import discord
from discord.ext import commands
import logging
import asyncio
import aiosqlite
from bot.utils import create_embed, format_points

logger = logging.getLogger(__name__)

def setup_commands(bot):
    """Set up all bot commands"""

    @bot.command(name='pontos', aliases=['p'])
    async def pontos_command(ctx, member: discord.Member | None = None):
        """Verificar pontos seus ou de outro usuário"""
        target = member if member is not None else ctx.author

        try:
            user_data = await bot.db.get_user_points(target.id)

            if not user_data:
                embed = create_embed(
                    "Sem Dados",
                    f"{target.display_name} ainda não ganhou nenhum ponto!",
                    discord.Color.orange()
                )
                await ctx.send(embed=embed)
                return

            username, total_points, msg_count, reactions_given, reactions_received, voice_minutes = user_data
            rank = await bot.db.get_user_rank(target.id)

            embed = create_embed(
                f"Pontos de {target.display_name}",
                f"**{format_points(total_points)}**",
                discord.Color.dark_purple()
            )

            embed.add_field(
                name="📊 Estatísticas",
                value=f"**Posição:** #{rank}\n",
                inline=False
            )

            embed.set_thumbnail(url=target.display_avatar.url)
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in pontos command: {e}")
            await ctx.send("❌ Ocorreu um erro ao buscar os dados de pontos.")

    @bot.command(name='ranking', aliases=['rank', 'top'])
    async def ranking_command(ctx, limit: int = 10):
        """Mostrar o ranking de pontos"""
        if limit > 25:
            limit = 25
        elif limit < 1:
            limit = 10

        try:
            leaderboard = await bot.db.get_leaderboard(limit)

            if not leaderboard:
                embed = create_embed(
                    "Ranking",
                    "Nenhum usuário ganhou pontos ainda!",
                    discord.Color.dark_purple()
                )
                await ctx.send(embed=embed)
                return

            embed = create_embed(
                f"🏆 Top {len(leaderboard)} Usuários",
                "",
                discord.Color.dark_purple()
            )

            description_lines = []
            for i, (username, points, user_id) in enumerate(leaderboard, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                description_lines.append(f"{medal} **{username}** - {format_points(points)}")

            embed.description = "\n".join(description_lines)

            if ctx.author.id not in [user_id for _, _, user_id in leaderboard]:
                user_rank = await bot.db.get_user_rank(ctx.author.id)
                if user_rank:
                    embed.set_footer(text=f"Sua posição: #{user_rank}")

            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in ranking command: {e}")
            await ctx.send("❌ Ocorreu um erro ao buscar os dados do ranking.")

    @bot.command(name='ajuda')
    async def ajuda_command(ctx):
        """Mostrar informações de ajuda"""
        embed = create_embed(
            "🤖 Bot de Pontos - Ajuda",
            "Ganhe pontos sendo ativo no servidor!",
            discord.Color.dark_purple()
        )

        embed.add_field(
            name="📈 Como Ganhar Pontos",
            value=f"**{bot.config['points']['message']}** ponto por mensagem\n"
                  f"**Cooldown:** {bot.config.get('cooldowns', {}).get('message_points_cooldown', 60)} segundos entre pontos",
            inline=False
        )

        embed.add_field(
            name="🎯 Comandos",
            value=f"`{bot.command_prefix}pontos [@usuário]` - Verificar pontos\n"
                  f"`{bot.command_prefix}ranking [número]` - Ver ranking\n"
                  f"`{bot.command_prefix}ajuda` - Mostrar esta ajuda",
            inline=False
        )

        user_display_name = ctx.author.display_name
        admin_users = bot.config.get('permissions', {}).get('admin_users', [])
        moderator_roles = bot.config.get('permissions', {}).get('moderator_roles', [])

        is_admin = user_display_name in admin_users
        is_moderator = any(role.name in moderator_roles for role in ctx.author.roles)

        if is_admin or is_moderator:
            embed.add_field(
                name="🔧 Comandos só da Administração",
                value=f"`{bot.command_prefix}resetuser @usuário` - Resetar pontos de um usuário",
                inline=False
            )

        embed.set_footer(text="Os pontos são atualizados em tempo real!")
        await ctx.send(embed=embed)

    @bot.command(name='resetpontos')
    async def reset_pontos_command(ctx):
        """Resetar todos os pontos (apenas admins/moderadores)"""
        user_display_name = ctx.author.display_name
        admin_users = bot.config.get('permissions', {}).get('admin_users', [])
        moderator_roles = bot.config.get('permissions', {}).get('moderator_roles', [])

        is_admin = user_display_name in admin_users
        is_moderator = any(role.name in moderator_roles for role in ctx.author.roles)

        if not is_admin and not is_moderator:
            await ctx.send("❌ Você não tem permissão para usar este comando.")
            return

        embed = create_embed(
            "⚠️ Confirmar Reset de Pontos",
            "Tem certeza que deseja resetar TODOS os pontos de TODOS os usuários?\n\n"
            "**Esta ação não pode ser desfeita!**\n\n"
            "Digite `confirmar` para prosseguir ou `cancelar` para cancelar.",
            discord.Color.dark_red()
        )
        await ctx.send(embed=embed)

        def check(message):
            return (message.author == ctx.author and 
                   message.channel == ctx.channel and
                   message.content.lower() in ['confirmar', 'cancelar'])

        try:
            response = await bot.wait_for('message', check=check, timeout=30.0)

            if response.content.lower() == 'cancelar':
                await ctx.send("✅ Reset de pontos cancelado.")
                return

            try:
                async with aiosqlite.connect(bot.db.db_path) as db:
                    await db.execute("UPDATE users SET total_points = 0")
                    await db.execute("DELETE FROM point_history")
                    await db.commit()

                embed = create_embed(
                    "✅ Reset Concluído",
                    f"Todos os pontos foram resetados por {ctx.author.display_name}",
                    discord.Color.purple()
                )
                await ctx.send(embed=embed)
                logger.info(f"Points reset executed by {ctx.author.display_name} ({ctx.author.id})")

            except Exception as e:
                logger.error(f"Error resetting points: {e}")
                await ctx.send("❌ Erro ao resetar pontos. Verifique os logs.")

        except asyncio.TimeoutError:
            await ctx.send("⏰ Tempo esgotado. Reset cancelado.")
