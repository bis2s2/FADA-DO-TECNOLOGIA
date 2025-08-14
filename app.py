import os
from flask import Flask, render_template, request, jsonify
from analyzer import analyze_discord_bot_code
from report_generator import ReportGenerator
from code_reviewer import CodeReviewer

app = Flask(__name__)

# Código do bot Discord para análise (exemplo)
DISCORD_BOT_CODE = """import discord
from discord.ext import commands
import logging
import asyncio
from bot.utils import create_embed, format_points

# Logger para registrar erros e eventos
logger = logging.getLogger(__name__)

def setup_commands(bot):
    \"\"\"Configura todos os comandos do bot\"\"\"

    # -------------------------------------------------------------------------
    # Comando: !pontos [@usuário]
    # Mostra os pontos do autor ou de outro usuário mencionado
    # -------------------------------------------------------------------------
    @bot.command(name='pontos', aliases=['p'])
    async def pontos_command(ctx, member: discord.Member | None = None):
        target = member if member is not None else ctx.author
        
        try:
            user_data = await bot.db.get_user_points(target.id)
            
            if not user_data:
                # Caso o usuário não tenha pontos
                embed = create_embed(
                    "Sem Dados",
                    f"{target.display_name} ainda não ganhou nenhum ponto!",
                    discord.Color.orange()
                )
                await ctx.send(embed=embed)
                return
            
            # Dados retornados do banco
            username, total_points, msg_count, reactions_given, reactions_received, voice_minutes = user_data
            rank = await bot.db.get_user_rank(target.id)
            
            # Monta o embed com as informações
            embed = create_embed(
                f"Pontos de {target.display_name}",
                f"**{format_points(total_points)}**",
                discord.Color.blue()
            )
            
            embed.add_field(
                name="📊 Estatísticas",
                value=f"**Posição:** #{rank}\\n"
                      f"**Mensagens:** {msg_count:,}",
                inline=False
            )
            
            embed.set_thumbnail(url=target.display_avatar.url)
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in pontos command: {e}")
            await ctx.send("❌ Ocorreu um erro ao buscar os dados de pontos.")

    # -------------------------------------------------------------------------
    # Comando: !ranking [número]
    # Mostra o ranking dos usuários com mais pontos
    # -------------------------------------------------------------------------
    @bot.command(name='ranking', aliases=['rank', 'top'])
    async def ranking_command(ctx, limit: int = 10):
        # Limita entre 1 e 25 posições
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
                    discord.Color.orange()
                )
                await ctx.send(embed=embed)
                return
            
            embed = create_embed(
                f"🏆 Top {len(leaderboard)} Usuários",
                "",
                discord.Color.gold()
            )
            
            # Cria lista formatada de ranking
            description_lines = []
            for i, (username, points, user_id) in enumerate(leaderboard, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                description_lines.append(f"{medal} **{username}** - {format_points(points)}")
            
            embed.description = "\\n".join(description_lines)
            
            # Mostra a posição do usuário caso não esteja no top exibido
            if ctx.author.id not in [user_id for _, _, user_id in leaderboard]:
                user_rank = await bot.db.get_user_rank(ctx.author.id)
                if user_rank:
                    embed.set_footer(text=f"Sua posição: #{user_rank}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in ranking command: {e}")
            await ctx.send("❌ Ocorreu um erro ao buscar os dados do ranking.")

    # -------------------------------------------------------------------------
    # Comando: !resetpontos
    # Reseta todos os pontos (somente admin/mod)
    # -------------------------------------------------------------------------
    @bot.command(name='resetpontos')
    async def reset_pontos_command(ctx):
        # Verifica permissão
        admin_users = bot.config.get('permissions', {}).get('admin_users', [])
        moderator_roles = bot.config.get('permissions', {}).get('moderator_roles', [])
        
        is_admin = ctx.author.display_name in admin_users
        is_moderator = any(role.name in moderator_roles for role in ctx.author.roles)
        
        if not is_admin and not is_moderator:
            await ctx.send("❌ Você não tem permissão para usar este comando.")
            return
        
        # Confirmação
        embed = create_embed(
            "⚠️ Confirmar Reset de Pontos",
            "Tem certeza que deseja resetar TODOS os pontos?\\n"
            "**Esta ação não pode ser desfeita!**\\n"
            "Digite `confirmar` para prosseguir ou `cancelar` para cancelar.",
            discord.Color.red()
        )
        await ctx.send(embed=embed)
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.lower() in ['confirmar', 'cancelar']
        
        try:
            response = await bot.wait_for('message', check=check, timeout=30.0)
            
            if response.content.lower() == 'cancelar':
                await ctx.send("✅ Reset de pontos cancelado.")
                return
            
            # Executa reset
            import aiosqlite
            async with aiosqlite.connect(bot.db.db_path) as db:
                await db.execute("UPDATE users SET total_points = 0")
                await db.execute("DELETE FROM point_history")
                await db.commit()
            
            embed = create_embed(
                "✅ Reset Concluído",
                f"Todos os pontos foram resetados por {ctx.author.display_name}",
                discord.Color.green()
            )
            await ctx.send(embed=embed)
            logger.info(f"Points reset executed by {ctx.author.display_name} ({ctx.author.id})")
                
        except asyncio.TimeoutError:
            await ctx.send("⏰ Tempo esgotado. Reset cancelado.")
        except Exception as e:
            logger.error(f"Error resetting points: {e}")
            await ctx.send("❌ Erro ao resetar pontos. Verifique os logs.")

    # -------------------------------------------------------------------------
    # Comando: !resetuser @usuário
    # Reseta pontos de um único usuário (somente admin/mod)
    # -------------------------------------------------------------------------
    @bot.command(name='resetuser')
    async def reset_user_command(ctx, member: discord.Member):
        # Verifica permissão
        admin_users = bot.config.get('permissions', {}).get('admin_users', [])
        moderator_roles = bot.config.get('permissions', {}).get('moderator_roles', [])
        
        is_admin = ctx.author.display_name in admin_users
        is_moderator = any(role.name in moderator_roles for role in ctx.author.roles)
        
        if not is_admin and not is_moderator:
            await ctx.send("❌ Você não tem permissão para usar este comando.")
            return
        
        if not member:
            await ctx.send("❌ Você precisa mencionar um usuário válido.")
            return
        
        # Confirmação
        embed = create_embed(
            "⚠️ Confirmar Reset de Usuário",
            f"Tem certeza que deseja resetar os pontos de **{member.display_name}**?\\n"
            "**Esta ação não pode ser desfeita!**\\n"
            "Digite `confirmar` para prosseguir ou `cancelar` para cancelar.",
            discord.Color.orange()
        )
        await ctx.send(embed=embed)
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.lower() in ['confirmar', 'cancelar']
        
        try:
            response = await bot.wait_for('message', check=check, timeout=30.0)
            
            if response.content.lower() == 'cancelar':
                await ctx.send("✅ Reset de usuário cancelado.")
                return
            
            # Executa reset do usuário
            import aiosqlite
            async with aiosqlite.connect(bot.db.db_path) as db:
                cursor = await db.execute("SELECT total_points FROM users WHERE user_id = ?", (member.id,))
                result = await cursor.fetchone()
                old_points = result[0] if result else 0
                
                await db.execute("UPDATE users SET total_points = 0 WHERE user_id = ?", (member.id,))
                await db.execute("DELETE FROM point_history WHERE user_id = ?", (member.id,))
                await db.commit()
            
            embed = create_embed(
                "✅ Reset de Usuário Concluído",
                f"Pontos de **{member.display_name}** resetados por {ctx.author.display_name}\\n"
                f"Pontos anteriores: {old_points:,}",
                discord.Color.green()
            )
            await ctx.send(embed=embed)
            logger.info(f"User {member.display_name} ({member.id}) points reset by {ctx.author.display_name} ({ctx.author.id}). Old points: {old_points}")
                
        except asyncio.TimeoutError:
            await ctx.send("⏰ Tempo esgotado. Reset cancelado.")
        except Exception as e:
            logger.error(f"Error resetting user points: {e}")
            await ctx.send("❌ Erro ao resetar pontos do usuário. Verifique os logs.")

    # -------------------------------------------------------------------------
    # Tratamento de erros globais dos comandos
    # -------------------------------------------------------------------------
    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return  # Ignora comandos inexistentes
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Argumento obrigatório não fornecido. Use `!ajuda`.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Argumento inválido. Use `!ajuda`.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Comando em cooldown. Tente novamente em {error.retry_after:.1f} segundos.")
        else:
            logger.error(f"Command error: {error}")
            await ctx.send("❌ Ocorreu um erro inesperado.")
"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_code():
    try:
        # Analisa o código
        analysis_report = analyze_discord_bot_code(DISCORD_BOT_CODE)
        
        # Gera relatório HTML
        report_generator = ReportGenerator(analysis_report)
        html_report = report_generator.generate_html_report()
        summary = report_generator.generate_summary()
        
        # Gera sugestões de refatoração
        code_reviewer = CodeReviewer(DISCORD_BOT_CODE)
        refactoring_suggestions = code_reviewer.get_refactoring_suggestions()
        security_fixes = code_reviewer.get_security_fixes()
        improved_code = code_reviewer.generate_improved_code()
        
        return jsonify({
            'success': True,
            'html_report': html_report,
            'summary': summary,
            'refactoring_suggestions': refactoring_suggestions,
            'security_fixes': security_fixes,
            'improved_code': improved_code,
            'raw_analysis': analysis_report
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/improved-code')
def get_improved_code():
    try:
        code_reviewer = CodeReviewer(DISCORD_BOT_CODE)
        improved_code = code_reviewer.generate_improved_code()
        
        return jsonify({
            'success': True,
            'improved_code': improved_code
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
