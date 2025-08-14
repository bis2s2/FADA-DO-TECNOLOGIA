import ast
import re
import json
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class IssueType(Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"
    BEST_PRACTICE = "best_practice"
    MAINTAINABILITY = "maintainability"

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class Issue:
    type: IssueType
    severity: Severity
    line_number: int
    description: str
    code_snippet: str
    suggestion: str
    category: str

class DiscordBotAnalyzer:
    def __init__(self, code_content: str):
        self.code_content = code_content
        self.lines = code_content.split('\n')
        self.issues = []
        
    def analyze(self) -> List[Issue]:
        """Executa análise completa do código"""
        self._analyze_imports()
        self._analyze_error_handling()
        self._analyze_security()
        self._analyze_database_operations()
        self._analyze_discord_api_usage()
        self._analyze_code_quality()
        self._analyze_performance()
        self._analyze_best_practices()
        
        return self.issues
    
    def _add_issue(self, issue_type: IssueType, severity: Severity, line_num: int, 
                   description: str, suggestion: str, category: str):
        """Adiciona uma issue à lista"""
        code_snippet = self.lines[line_num - 1] if 0 < line_num <= len(self.lines) else ""
        issue = Issue(
            type=issue_type,
            severity=severity,
            line_number=line_num,
            description=description,
            code_snippet=code_snippet.strip(),
            suggestion=suggestion,
            category=category
        )
        self.issues.append(issue)
    
    def _analyze_imports(self):
        """Analisa imports e dependências"""
        for i, line in enumerate(self.lines, 1):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                # Verifica imports inline desnecessários
                if 'import aiosqlite' in line and i > 200:
                    self._add_issue(
                        IssueType.CODE_QUALITY,
                        Severity.MEDIUM,
                        i,
                        "Import inline de aiosqlite - deveria estar no topo do arquivo",
                        "Mova todos os imports para o início do arquivo",
                        "Organização de Código"
                    )
    
    def _analyze_error_handling(self):
        """Analisa tratamento de erros"""
        in_try_block = False
        try_line = 0
        
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            
            if stripped.startswith('try:'):
                in_try_block = True
                try_line = i
                
            elif stripped.startswith('except Exception as e:'):
                if in_try_block:
                    # Verifica se há logging adequado
                    next_lines = self.lines[i:i+5]
                    has_logging = any('logger.' in l for l in next_lines)
                    
                    if not has_logging:
                        self._add_issue(
                            IssueType.BEST_PRACTICE,
                            Severity.MEDIUM,
                            i,
                            "Exception capturada mas não logada adequadamente",
                            "Adicione logging detalhado para facilitar debugging",
                            "Tratamento de Erros"
                        )
                
                in_try_block = False
                
            elif 'await ctx.send(' in stripped and 'erro' in stripped.lower():
                # Mensagens de erro muito genéricas
                if '❌ Ocorreu um erro' in line:
                    self._add_issue(
                        IssueType.CODE_QUALITY,
                        Severity.LOW,
                        i,
                        "Mensagem de erro muito genérica para o usuário",
                        "Forneça mensagens de erro mais específicas quando possível",
                        "UX/Usabilidade"
                    )
    
    def _analyze_security(self):
        """Analisa questões de segurança"""
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            
            # Verificação de permissões por display_name (inseguro)
            if 'ctx.author.display_name in admin_users' in stripped:
                self._add_issue(
                    IssueType.SECURITY,
                    Severity.HIGH,
                    i,
                    "Verificação de permissão usando display_name é insegura",
                    "Use ctx.author.id em vez de display_name para verificação de permissões",
                    "Autenticação e Autorização"
                )
            
            # SQL direto sem prepared statements adequados
            if 'await db.execute(' in stripped and '"' in stripped:
                # Verifica se há concatenação de strings
                if '+' in stripped or 'f"' in stripped:
                    self._add_issue(
                        IssueType.SECURITY,
                        Severity.CRITICAL,
                        i,
                        "Possível vulnerabilidade de SQL Injection",
                        "Use sempre prepared statements com placeholders (?)",
                        "Segurança de Dados"
                    )
            
            # Timeout muito baixo pode causar problemas
            if 'timeout=30.0' in stripped:
                self._add_issue(
                    IssueType.PERFORMANCE,
                    Severity.LOW,
                    i,
                    "Timeout de 30 segundos pode ser insuficiente em algumas situações",
                    "Considere aumentar o timeout ou torná-lo configurável",
                    "Performance"
                )
    
    def _analyze_database_operations(self):
        """Analisa operações de banco de dados"""
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            
            # Operações de DB sem transação adequada
            if 'async with aiosqlite.connect(' in stripped:
                # Verifica se há multiple operations sem transação explícita
                next_lines = self.lines[i:i+10]
                execute_count = sum(1 for l in next_lines if 'await db.execute(' in l)
                
                if execute_count > 1:
                    has_commit = any('await db.commit()' in l for l in next_lines)
                    if not has_commit:
                        self._add_issue(
                            IssueType.BUG,
                            Severity.HIGH,
                            i,
                            "Múltiplas operações de banco sem commit explícito",
                            "Adicione await db.commit() após as operações de escrita",
                            "Banco de Dados"
                        )
            
            # Queries que podem ser otimizadas
            if 'SELECT total_points FROM users WHERE user_id = ?' in stripped:
                self._add_issue(
                    IssueType.PERFORMANCE,
                    Severity.LOW,
                    i,
                    "Query poderia usar índice para melhor performance",
                    "Certifique-se de que existe um índice na coluna user_id",
                    "Otimização de Banco"
                )
    
    def _analyze_discord_api_usage(self):
        """Analisa uso da API do Discord"""
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            
            # Verificação de member None após conversão
            if 'member: discord.Member | None = None' in stripped:
                # Verifica se há validação adequada
                next_lines = self.lines[i:i+10]
                has_validation = any('if not member:' in l for l in next_lines)
                
                if not has_validation and 'member.id' in ' '.join(next_lines):
                    self._add_issue(
                        IssueType.BUG,
                        Severity.MEDIUM,
                        i,
                        "Possível acesso a member None sem validação",
                        "Sempre valide se member não é None antes de usar",
                        "API do Discord"
                    )
            
            # Rate limiting considerations
            if 'await ctx.send(' in stripped:
                self._add_issue(
                    IssueType.BEST_PRACTICE,
                    Severity.INFO,
                    i,
                    "Considere implementar rate limiting para comandos",
                    "Implemente cooldowns para evitar spam de comandos",
                    "Rate Limiting"
                )
    
    def _analyze_code_quality(self):
        """Analisa qualidade do código"""
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            
            # Linhas muito longas
            if len(line) > 100:
                self._add_issue(
                    IssueType.CODE_QUALITY,
                    Severity.LOW,
                    i,
                    f"Linha muito longa ({len(line)} caracteres)",
                    "Quebre linhas longas em múltiplas linhas para melhor legibilidade",
                    "Formatação"
                )
            
            # Magic numbers
            if re.search(r'\b(25|60)\b', stripped) and 'limit' in stripped:
                self._add_issue(
                    IssueType.CODE_QUALITY,
                    Severity.LOW,
                    i,
                    "Uso de números mágicos no código",
                    "Defina constantes para valores numéricos importantes",
                    "Manutenibilidade"
                )
            
            # Duplicação de código
            if 'is_admin = ctx.author.display_name in admin_users' in stripped:
                self._add_issue(
                    IssueType.CODE_QUALITY,
                    Severity.MEDIUM,
                    i,
                    "Lógica de verificação de permissão duplicada",
                    "Crie uma função helper para verificação de permissões",
                    "DRY Principle"
                )
    
    def _analyze_performance(self):
        """Analisa questões de performance"""
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            
            # Queries desnecessárias em loops
            if 'for i, (username, points, user_id) in enumerate(leaderboard' in stripped:
                next_lines = self.lines[i:i+5]
                if any('await bot.db.' in l for l in next_lines):
                    self._add_issue(
                        IssueType.PERFORMANCE,
                        Severity.MEDIUM,
                        i,
                        "Possível N+1 query problem em loop",
                        "Otimize queries para buscar todos os dados de uma vez",
                        "Otimização de Queries"
                    )
    
    def _analyze_best_practices(self):
        """Analisa aderência às melhores práticas"""
        # Verifica se há docstrings adequadas
        function_lines = [i for i, line in enumerate(self.lines, 1) if 'async def ' in line or 'def ' in line]
        
        for func_line in function_lines:
            if func_line + 1 < len(self.lines):
                next_line = self.lines[func_line].strip()
                if not next_line.startswith('"""') and not next_line.startswith("'''"):
                    self._add_issue(
                        IssueType.BEST_PRACTICE,
                        Severity.LOW,
                        func_line,
                        "Função sem docstring",
                        "Adicione docstrings descrevendo o propósito e parâmetros da função",
                        "Documentação"
                    )

def analyze_discord_bot_code(code_content: str) -> Dict[str, Any]:
    """Analisa o código do bot Discord e retorna relatório completo"""
    analyzer = DiscordBotAnalyzer(code_content)
    issues = analyzer.analyze()
    
    # Organiza issues por categoria e severidade
    report = {
        'total_issues': len(issues),
        'by_severity': {},
        'by_type': {},
        'by_category': {},
        'issues': []
    }
    
    for issue in issues:
        # Por severidade
        sev = issue.severity.value
        if sev not in report['by_severity']:
            report['by_severity'][sev] = 0
        report['by_severity'][sev] += 1
        
        # Por tipo
        typ = issue.type.value
        if typ not in report['by_type']:
            report['by_type'][typ] = 0
        report['by_type'][typ] += 1
        
        # Por categoria
        cat = issue.category
        if cat not in report['by_category']:
            report['by_category'][cat] = 0
        report['by_category'][cat] += 1
        
        # Adiciona ao relatório
        report['issues'].append({
            'type': issue.type.value,
            'severity': issue.severity.value,
            'line': issue.line_number,
            'description': issue.description,
            'code': issue.code_snippet,
            'suggestion': issue.suggestion,
            'category': issue.category
        })
    
    # Ordena issues por severidade e linha
    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
    report['issues'].sort(key=lambda x: (severity_order[x['severity']], x['line']))
    
    return report
