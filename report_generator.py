from typing import Dict, Any, List
import json
from datetime import datetime

class ReportGenerator:
    def __init__(self, analysis_report: Dict[str, Any]):
        self.report = analysis_report
        
    def generate_html_report(self) -> str:
        """Gera relatório HTML detalhado"""
        severity_colors = {
            'critical': '#dc2626',
            'high': '#ea580c',
            'medium': '#d97706',
            'low': '#65a30d',
            'info': '#0284c7'
        }
        
        severity_icons = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '🔶',
            'low': '💡',
            'info': 'ℹ️'
        }
        
        # Estatísticas gerais
        stats_html = self._generate_stats_section()
        
        # Issues por categoria
        issues_html = ""
        current_category = None
        
        for issue in self.report['issues']:
            if issue['category'] != current_category:
                if current_category is not None:
                    issues_html += "</div>"
                current_category = issue['category']
                issues_html += f"""
                <div class="category-section">
                    <h3 class="category-title">{current_category}</h3>
                """
            
            severity = issue['severity']
            icon = severity_icons.get(severity, '•')
            color = severity_colors.get(severity, '#6b7280')
            
            issues_html += f"""
            <div class="issue-card severity-{severity}">
                <div class="issue-header">
                    <span class="severity-badge" style="background-color: {color}">
                        {icon} {severity.upper()}
                    </span>
                    <span class="line-number">Linha {issue['line']}</span>
                </div>
                <h4 class="issue-title">{issue['description']}</h4>
                <div class="code-snippet">
                    <pre><code>{issue['code']}</code></pre>
                </div>
                <div class="suggestion">
                    <strong>💡 Sugestão:</strong> {issue['suggestion']}
                </div>
            </div>
            """
        
        if current_category is not None:
            issues_html += "</div>"
        
        return f"""
        <div class="report-content">
            <div class="report-header">
                <h1>🤖 Análise do Bot Discord</h1>
                <p class="report-date">Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
            </div>
            
            {stats_html}
            
            <div class="issues-section">
                <h2>📋 Issues Encontradas</h2>
                {issues_html}
            </div>
            
            <div class="recommendations-section">
                <h2>🎯 Recomendações Gerais</h2>
                {self._generate_recommendations()}
            </div>
        </div>
        """
    
    def _generate_stats_section(self) -> str:
        """Gera seção de estatísticas"""
        total = self.report['total_issues']
        by_severity = self.report['by_severity']
        
        stats_cards = ""
        for severity, count in by_severity.items():
            percentage = (count / total * 100) if total > 0 else 0
            stats_cards += f"""
            <div class="stat-card severity-{severity}">
                <div class="stat-number">{count}</div>
                <div class="stat-label">{severity.title()}</div>
                <div class="stat-percentage">{percentage:.1f}%</div>
            </div>
            """
        
        return f"""
        <div class="stats-section">
            <h2>📊 Resumo da Análise</h2>
            <div class="stats-grid">
                <div class="stat-card total">
                    <div class="stat-number">{total}</div>
                    <div class="stat-label">Total de Issues</div>
                </div>
                {stats_cards}
            </div>
        </div>
        """
    
    def _generate_recommendations(self) -> str:
        """Gera recomendações gerais baseadas na análise"""
        recommendations = []
        
        # Baseado nos problemas encontrados
        if self.report['by_severity'].get('critical', 0) > 0:
            recommendations.append({
                'title': '🚨 Issues Críticas',
                'text': 'Há problemas críticos que devem ser corrigidos imediatamente, principalmente relacionados à segurança.'
            })
        
        if self.report['by_category'].get('Autenticação e Autorização', 0) > 0:
            recommendations.append({
                'title': '🔐 Segurança de Autenticação',
                'text': 'Implemente verificações de permissão baseadas em IDs de usuário em vez de nomes de exibição.'
            })
        
        if self.report['by_category'].get('DRY Principle', 0) > 0:
            recommendations.append({
                'title': '♻️ Refatoração',
                'text': 'Crie funções helper para lógicas repetitivas, especialmente verificação de permissões.'
            })
        
        if self.report['by_type'].get('performance', 0) > 0:
            recommendations.append({
                'title': '⚡ Performance',
                'text': 'Otimize queries de banco de dados e considere implementar cache para dados frequentemente acessados.'
            })
        
        # Recomendações gerais sempre aplicáveis
        recommendations.extend([
            {
                'title': '📝 Logs e Monitoramento',
                'text': 'Implemente logging estruturado e considere usar ferramentas de monitoramento para produção.'
            },
            {
                'title': '🧪 Testes',
                'text': 'Adicione testes unitários e de integração para garantir a qualidade do código.'
            },
            {
                'title': '📚 Documentação',
                'text': 'Documente as funções e mantenha um README atualizado com instruções de instalação e uso.'
            }
        ])
        
        rec_html = ""
        for rec in recommendations:
            rec_html += f"""
            <div class="recommendation-card">
                <h4>{rec['title']}</h4>
                <p>{rec['text']}</p>
            </div>
            """
        
        return f'<div class="recommendations-grid">{rec_html}</div>'
    
    def generate_json_report(self) -> str:
        """Gera relatório em formato JSON"""
        return json.dumps(self.report, indent=2, ensure_ascii=False)
    
    def generate_summary(self) -> Dict[str, Any]:
        """Gera resumo executivo da análise"""
        critical_issues = [issue for issue in self.report['issues'] if issue['severity'] == 'critical']
        high_issues = [issue for issue in self.report['issues'] if issue['severity'] == 'high']
        
        return {
            'total_issues': self.report['total_issues'],
            'critical_count': len(critical_issues),
            'high_count': len(high_issues),
            'most_common_category': max(self.report['by_category'].keys(), 
                                      key=lambda k: self.report['by_category'][k]) if self.report['by_category'] else 'N/A',
            'priority_fixes': [issue['description'] for issue in critical_issues + high_issues][:5],
            'overall_health': self._calculate_health_score()
        }
    
    def _calculate_health_score(self) -> str:
        """Calcula score geral da saúde do código"""
        total = self.report['total_issues']
        critical = self.report['by_severity'].get('critical', 0)
        high = self.report['by_severity'].get('high', 0)
        medium = self.report['by_severity'].get('medium', 0)
        
        # Score baseado na severidade dos problemas
        penalty = (critical * 10) + (high * 5) + (medium * 2)
        
        if penalty == 0:
            return "Excelente"
        elif penalty < 10:
            return "Bom"
        elif penalty < 25:
            return "Regular"
        elif penalty < 50:
            return "Ruim"
        else:
            return "Crítico"
