import re
from typing import List, Dict, Any

class CodeReviewer:
    """Classe para revisar e sugerir melhorias específicas no código"""
    
    def __init__(self, code_content: str):
        self.code = code_content
        self.lines = code_content.split('\n')
        
    def generate_improved_code(self) -> str:
        """Gera versão melhorada do código com correções aplicadas"""
        improved_lines = []
        i = 0
        
        # Adicionar imports no topo
        improved_lines.extend([
            "import discord",
            "from discord.ext import commands",
            "import logging",
            "import asyncio",
            "import aiosqlite",
            "from bot.utils import create_embed, format_points",
            "from typing import Optional",
            "",
            "# Logger para registrar erros e eventos",
            "logger = logging.getLogger(__name__)",
            "",
            "# Constantes",
            "MAX_RANKING_LIMIT = 25",
            "DEFAULT_RANKING_LIMIT = 10",
            "CONFIRMATION_TIMEOUT = 30.0",
            "",
            "async def check_permissions(ctx, bot) -> bool:",
            '    """Helper function para verificar permissões de admin/moderator"""',
            "    admin_users = bot.config.get('permissions', {}).get('admin_users', [])",
            "    moderator_roles = bot.config.get('permissions', {}).get('moderator_roles', [])",
            "    ",
            "    # Usar ID em vez de display_name para segurança",
            "    is_admin = ctx.author.id in admin_users",
            "    is_moderator = any(role.name in moderator_roles for role in ctx.author.roles)",
            "    ",
            "    return is_admin or is_moderator",
            "",
        ])
        
        # Processar o resto do código com melhorias
        skip_until = 0
        for i, line in enumerate(self.lines):
            if i < skip_until:
                continue
                
            # Pular imports originais já adicionados no topo
            if (line.strip().startswith('import ') or 
                line.strip().startswith('from ') or
                line.strip() == "logger = logging.getLogger(__name__)"):
                continue
            
            # Melhorar função setup_commands
            if 'def setup_commands(bot):' in line:
                improved_lines.extend([
                    'def setup_commands(bot):',
                    '    """Configura todos os comandos do bot"""',
                    '',
                ])
                continue
            
            # Melhorar comando pontos
            if '@bot.command(name=\'pontos\', aliases=[\'p\'])' in line:
                improved_lines.extend([
                    "    @bot.command(name='pontos', aliases=['p'])",
                    "    async def pontos_command(ctx, member: Optional[discord.Member] = None):",
                    '        """',
                    '        Mostra os pontos do autor ou de outro usuário mencionado',
                    '        ',
                    '        Args:',
                    '            member: Membro opcional para consultar pontos',
                    '        """',
                ])
                # Pular linha original da função
                skip_until = i + 2
                continue
            
            # Melhorar verificações de permissão
            if 'is_admin = ctx.author.display_name in admin_users' in line:
                improved_lines.extend([
                    "        if not await check_permissions(ctx, bot):",
                    "            await ctx.send('❌ Você não tem permissão para usar este comando.')",
                    "            return",
                ])
                # Pular linhas de verificação originais
                j = i + 1
                while j < len(self.lines) and ('is_moderator' in self.lines[j] or 
                                               'if not is_admin and not is_moderator' in self.lines[j]):
                    j += 1
                skip_until = j
                continue
            
            # Melhorar constantes mágicas
            line = line.replace('limit > 25', f'limit > MAX_RANKING_LIMIT')
            line = line.replace('limit = 25', f'limit = MAX_RANKING_LIMIT')
            line = line.replace('limit = 10', f'limit = DEFAULT_RANKING_LIMIT')
            line = line.replace('timeout=30.0', f'timeout=CONFIRMATION_TIMEOUT')
            
            # Adicionar validações melhoradas
            if 'if not member:' in line and 'resetuser' in self.lines[max(0, i-10):i+1]:
                improved_lines.extend([
                    "        if member is None:",
                    "            await ctx.send('❌ Você precisa mencionar um usuário válido.')",
                    "            return",
                ])
                continue
            
            improved_lines.append(line)
        
        return '\n'.join(improved_lines)
    
    def get_refactoring_suggestions(self) -> List[Dict[str, Any]]:
        """Retorna sugestões específicas de refatoração"""
        suggestions = []
        
        # Sugestão para função helper de permissões
        suggestions.append({
            'title': 'Criar função helper para verificação de permissões',
            'description': 'A lógica de verificação de admin/moderator está duplicada em vários comandos',
            'code_before': '''
is_admin = ctx.author.display_name in admin_users
is_moderator = any(role.name in moderator_roles for role in ctx.author.roles)

if not is_admin and not is_moderator:
    await ctx.send("❌ Você não tem permissão...")
    return
            '''.strip(),
            'code_after': '''
async def check_permissions(ctx, bot) -> bool:
    """Helper function para verificar permissões"""
    admin_users = bot.config.get('permissions', {}).get('admin_users', [])
    moderator_roles = bot.config.get('permissions', {}).get('moderator_roles', [])
    
    is_admin = ctx.author.id in admin_users  # Usar ID é mais seguro
    is_moderator = any(role.name in moderator_roles for role in ctx.author.roles)
    
    return is_admin or is_moderator

# Nos comandos:
if not await check_permissions(ctx, bot):
    await ctx.send("❌ Você não tem permissão...")
    return
            '''.strip(),
            'benefits': [
                'Reduz duplicação de código',
                'Melhora segurança usando IDs',
                'Facilita manutenção',
                'Torna testes mais fáceis'
            ]
        })
        
        # Sugestão para constantes
        suggestions.append({
            'title': 'Definir constantes para valores numéricos',
            'description': 'Números mágicos tornam o código menos manutenível',
            'code_before': '''
if limit > 25:
    limit = 25
elif limit < 1:
    limit = 10
            '''.strip(),
            'code_after': '''
# No topo do arquivo
MAX_RANKING_LIMIT = 25
DEFAULT_RANKING_LIMIT = 10
MIN_RANKING_LIMIT = 1

# No código
if limit > MAX_RANKING_LIMIT:
    limit = MAX_RANKING_LIMIT
elif limit < MIN_RANKING_LIMIT:
    limit = DEFAULT_RANKING_LIMIT
            '''.strip(),
            'benefits': [
                'Facilita alteração de valores',
                'Torna o código mais legível',
                'Reduz erros de digitação',
                'Melhora manutenibilidade'
            ]
        })
        
        # Sugestão para melhor tratamento de erros
        suggestions.append({
            'title': 'Melhorar tratamento de erros específicos',
            'description': 'Capturar exceções específicas em vez de Exception genérica',
            'code_before': '''
except Exception as e:
    logger.error(f"Error in pontos command: {e}")
    await ctx.send("❌ Ocorreu um erro ao buscar os dados de pontos.")
            '''.strip(),
            'code_after': '''
except aiosqlite.Error as e:
    logger.error(f"Database error in pontos command: {e}")
    await ctx.send("❌ Erro no banco de dados. Tente novamente.")
except discord.HTTPException as e:
    logger.error(f"Discord API error in pontos command: {e}")
    await ctx.send("❌ Erro de comunicação com Discord.")
except Exception as e:
    logger.error(f"Unexpected error in pontos command: {e}")
    await ctx.send("❌ Erro inesperado. Contacte um administrador.")
            '''.strip(),
            'benefits': [
                'Tratamento específico para cada tipo de erro',
                'Mensagens mais úteis para usuários',
                'Melhor debugging',
                'Recuperação mais inteligente'
            ]
        })
        
        return suggestions

    def get_security_fixes(self) -> List[Dict[str, str]]:
        """Retorna correções específicas de segurança"""
        fixes = []
        
        # Fix de autenticação
        fixes.append({
            'issue': 'Verificação de permissão insegura usando display_name',
            'risk': 'Usuários podem alterar display_name e burlar verificações',
            'fix': 'Usar ctx.author.id em vez de ctx.author.display_name',
            'code': '''
# ANTES (inseguro):
is_admin = ctx.author.display_name in admin_users

# DEPOIS (seguro):
admin_user_ids = bot.config.get('permissions', {}).get('admin_user_ids', [])
is_admin = ctx.author.id in admin_user_ids
            '''
        })
        
        # Fix de rate limiting
        fixes.append({
            'issue': 'Ausência de rate limiting em comandos',
            'risk': 'Usuários podem fazer spam de comandos sobrecarregando o bot',
            'fix': 'Implementar cooldowns nos comandos',
            'code': '''
from discord.ext import commands

@commands.cooldown(1, 5, commands.BucketType.user)
@bot.command(name='pontos')
async def pontos_command(ctx, member: Optional[discord.Member] = None):
    # comando aqui...
            '''
        })
        
        return fixes
