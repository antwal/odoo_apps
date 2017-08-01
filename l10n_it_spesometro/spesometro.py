# -*- coding: utf-8 -*-
##############################################################################
#    
#    Author: Alessandro Camilli (a.camilli@yahoo.it)
#    Copyright (C) 2014
#    Associazione OpenERP Italia (<http://www.openerp-italia.org>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, orm
from openerp.tools.translate import _
import decimal_precision as dp 
import datetime, time
from unittest import result

class res_country(orm.Model):
    _inherit = "res.country"
    _columns =  {
        'codice_stato_agenzia_entrate': fields.char('Codice stato Agenzia Entrate', size=3)
    }
    
class account_tax_code(orm.Model): 
    _inherit = "account.tax.code"
    _columns =  {
        'spesometro_escludi': fields.boolean('Escludi dalla dichiarazione'),
    }
    
    _defaults = {
        'spesometro_escludi' : False,
    }
    
class account_journal(orm.Model): 
    _inherit = "account.journal"
    _columns =  {
        'spesometro': fields.boolean('Da includere'),
        'spesometro_operazione': fields.selection((('FA','Operazioni documentate da fattura'), 
                                  ('SA','Operazioni senza fattura'),
                                  ('BL1','Operazioni con paesi con fiscalità privilegiata'),
                                  ('BL2','Operazioni con soggetti non residenti'),
                                  ('BL3','Acquisti di servizi da soggetti non residenti'),
                                  ('DR','Documento Riepilogativo')),
                   'Operazione' ),
        'spesometro_segno': fields.selection((('attiva','Attiva'), 
                                  ('passiva','Passiva')),
                   'Segno operaz.' ),
        'spesometro_IVA_non_esposta': fields.boolean('IVA non esposta')
    }

class res_partner(orm.Model):
    _inherit = "res.partner"
    _columns =  {
        'spesometro_escludi': fields.boolean('Escludi'),
        'spesometro_operazione': fields.selection((('FA','Operazioni documentate da fattura'), 
                                  ('SA','Operazioni senza fattura'),
                                  ('BL1','Operazioni con paesi con fiscalità privilegiata'),
                                  ('BL2','Operazioni con soggetti non residenti'),
                                  ('BL3','Acquisti di servizi da soggetti non residenti'),
                                  ('DR','Documento Riepilogativo')),
                   'Operazione' ),
        'spesometro_operazione_tipo_importo': fields.selection((
                                ('INE','Imponibile, Non Imponibile, Esente'), 
                                ('NS','Non Soggette ad IVA'),
                                ('NV','Note di variazione')),
                   'Tipo Importo' ),
        'spesometro_IVA_non_esposta': fields.boolean('IVA non esposta'),
        'spesometro_leasing': fields.selection((('A','Autovettura'), 
                                  ('B','Caravan'),
                                  ('C','Altri veicoli'),
                                  ('D','Unità da diporto'),
                                  ('E','Aeromobili')),
                   'Tipo Leasing' ),
        'spesometro_tipo_servizio': fields.selection((('cessione','Cessione Beni'), 
                                  ('servizi','Prestazione di servizi')),
                    'Tipo servizio', help="Specificare per 'Operazioni con soggetti non residenti' "),
    }
    
    _defaults = {
        'spesometro_escludi' : False,
    }

class spesometro_configurazione(orm.Model):
    
    def _check_one_year(self, cr, uid, ids, context=None):
        for element in self.browse(cr, uid, ids, context=context):
            element_ids = self.search(cr, uid, [('anno','=', element.anno)], context=context)
            if len(element_ids) > 1:
                return False
        return True
    
    _name = "spesometro.configurazione"
    _description = "Spesometro - Configurazione"
    _columns = {
        'anno': fields.integer('Anno', size=4, required=True ),
        'stato_san_marino': fields.many2one('res.country', 'Stato San Marino', required=True),
        'regole_ids': fields.one2many('spesometro.regole', 'configurazione_id',
                     'Regole'),
        'quadro_fa_limite_importo': fields.float('Quadro FA - Limite importo'),
        'quadro_fa_limite_importo_line': fields.float('Quadro FA - Limite importo singola operaz.'),
        'quadro_sa_limite_importo': fields.float('Quadro SA - Limite importo'),
        'quadro_sa_limite_importo_line': fields.float('Quadro SA - Limite importo singola operaz.'),
        'quadro_bl1_limite_importo': fields.float('Quadro BL - Operazioni con paesi con fiscalità privilegiata - Limite importo'),
        'quadro_bl1_limite_importo_line': fields.float('Quadro BL - Operazioni con paesi con fiscalità privilegiata - Limite importo singola operaz.'),
        'quadro_bl2_limite_importo': fields.float('Quadro BL - Operazioni con soggetti non residenti - Limite importo'),
        'quadro_bl2_limite_importo_line': fields.float('Quadro BL - Operazioni con soggetti non residenti - Limite importo singola operaz.'),
        'quadro_bl3_limite_importo': fields.float('Quadro BL - Acquisti di servizi da soggetti non residenti - Limite importo'),
        'quadro_bl3_limite_importo_line': fields.float('Quadro BL - Acquisti di servizi da soggetti non residenti - Limite importo singola operaz.'),
        'quadro_se_limite_importo_line': fields.float('Quadro SE - Limite importo singola operaz.'),
        }
    _constraints = [
        (_check_one_year, 'Error! Config for this year already exists.', ['anno']),
    ]

class spesometro_regole(orm.Model):
    
    def _check_one_choose(self, cr, uid, ids, context=None):
        for element in self.browse(cr, uid, ids, context=context):
            if not element.journal_id\
                    and not element.account_id\
                    and not element.partner_id:
                return False
        return True
    
    _name = "spesometro.regole"
    _description = "Spesometro - Regole"
    _columns = {
        'configurazione_id': fields.many2one('spesometro.configurazione',
                    'Configurazione',  required=True, readonly=True ),
        'active': fields.boolean('Active'),
        'note': fields.text('Note'),
        'sequence': fields.integer('Sequenza', required=True ),
        'move_id': fields.many2one('account.move', 'Move'),
        'journal_id': fields.many2one('account.journal', 'Journal'),
        'account_id': fields.many2one('account.account', 'Account'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'counterpart_id': fields.many2one('account.account', 'Counterpart'),
        'tipo_calcolo': fields.selection((
                                ('counterpart','Saldo Contropartita'), 
                                ('account_balance','Saldo Conto'),
                                ('account_credit','Conto Avere'),
                                ('account_debit','Conto Dare'),
                                ('invoice','Fattura'),
                                ),
                                'Tipo Calcolo',required=True),
        'no_limite_importo': fields.boolean('No limite importo'),
        'spesometro_partner_id': fields.many2one('res.partner', 'Partner sul quadro'),
        'spesometro_operazione': fields.selection((('FA','Quadro FA - Operazioni documentate da fattura'), 
                                  ('SA','Quadro SA - Operazioni senza fattura'),
                                  ('BL1','Quadro BL - Operazioni con paesi con fiscalità privilegiata'),
                                  ('BL2','Quadro BL - Operazioni con soggetti non residenti'),
                                  ('BL3','Quadro BL - Acquisti di servizi da soggetti non residenti'),
                                  ('DR','Documento Riepilogativo')),
                   'Operazione', required=True ),
        'spesometro_operazione_tipo_importo': fields.selection((
                                ('INE','Imponibile, Non Imponibile, Esente'), 
                                ('NS','Non Soggette ad IVA'),
                                ('NV','Note di variazione')),
                   'Tipo Importo' ),
        'spesometro_segno': fields.selection((
                                ('attiva','Attiva'), 
                                ('passiva','Passiva')),
                                'Segno'),
        'spesometro_IVA_non_esposta': fields.boolean('IVA non esposta'),
        'spesometro_leasing': fields.selection((('A','Autovettura'), 
                                  ('B','Caravan'),
                                  ('C','Altri veicoli'),
                                  ('D','Unità da diporto'),
                                  ('E','Aeromobili')),
                   'Tipo Leasing' ),
        'spesometro_tipo_servizio': fields.selection((('cessione','Cessione Beni'), 
                                  ('servizi','Prestazione di servizi')),
                    'Tipo servizio', help="Specificare per 'Operazioni con soggetti non residenti' "),
        }
    _constraints = [
        (_check_one_choose, 'Error! Any filter setting', ['sequence']),
    ]
    _order = "sequence"
    _defaults = {
        'active' : True
    }
    
    def get_importo(self, cr, uid, role_id, move):
        res = {
            'amount_untaxed' : 0,
            'amount_tax' : 0,
            'amount_total' : 0,
        }
        
        invoice_obj = self.pool['account.invoice']
        move_line_obj = self.pool['account.move.line']
        if not role_id:
            return 0
        importo = 0
        move_line_ids = []
        role = self.browse(cr, uid, role_id)
        #
        # Calcolo da righe registrazione
        #
        if not role.tipo_calcolo == 'invoice':
            # Selezione linee registrazione x calcolo
            if role.tipo_calcolo == 'counterpart':
                domain = [('move_id', '=', move.id),
                          ('account_id', '=', role.counterpart_id.id)]
                move_line_ids = move_line_obj.search(cr, uid, domain)
            elif role.tipo_calcolo == 'account_balance':
                domain = [('move_id', '=', move.id),
                          ('account_id', '=', role.account_id.id)]
                move_line_ids = move_line_obj.search(cr, uid, domain)
            elif role.tipo_calcolo == 'account_credit':
                domain = [('move_id', '=', move.id),
                          ('account_id', '=', role.account_id.id),
                          ('credit', '>', 0)]
                move_line_ids = move_line_obj.search(cr, uid, domain)
            elif role.tipo_calcolo == 'account_debit':
                domain = [('move_id', '=', move.id),
                          ('account_id', '=', role.account_id.id),
                          ('debit', '>', 0)]
                move_line_ids = move_line_obj.search(cr, uid, domain)
            # Calcolo
            for line in move_line_obj.browse(cr, uid, move_line_ids):
                if line.credit:
                    importo += line.credit
                else:
                    importo -= line.debit
            #if importo < 0:
            #    importo = importo * -1
            res['amount_total'] = round(importo, 2)
        #
        # Calcolo da fattura
        #
        else:
            domain = [('move_id', '=', move.id)]
            inv_ids = invoice_obj.search(cr, uid, domain)
            if inv_ids:
                inv = invoice_obj.browse(cr, uid, inv_ids[0])
                for line in inv.tax_line:
                    if not line.tax_code_id.spesometro_escludi:
                        res['amount_untaxed'] += line.base
                        res['amount_tax'] += line.amount
                        res['amount_total'] += round(line.base + line.amount, 2)
        
        return res
    
    def get_regola(self, cr, uid, move, invoice):
        '''
        Restituisce la prima regola valida seguendo la sequenza
        '''
        res = {}
        move_line_obj = self.pool['account.move.line']
        role_ids = self.search(cr, uid, [('active','=',True)])
        for role in self.browse(cr, uid, role_ids):
            # test move
            if role.move_id \
                    and role.move_id.id != move.id:
                continue
            # test journal
            if role.journal_id \
                    and role.journal_id.id != move.journal_id.id:
                continue
            # test account
            if role.account_id:
                domain = [('move_id', '=', move.id),
                          ('account_id', '=', role.account_id.id)]
                move_line_ids = move_line_obj.search(cr, uid, domain)
                if not move_line_ids:
                    continue
            # test partner
            if role.partner_id:
                domain = [('move_id', '=', move.id),
                          ('partner_id', '=', role.partner_id.id)]
                move_line_ids = move_line_obj.search(cr, uid, domain)
                if not move_line_ids:
                    continue
            # test counterpart
            if role.counterpart_id:
                domain = [('move_id', '=', move.id),
                          ('account_id', '=', role.counterpart_id.id)]
                move_line_ids = move_line_obj.search(cr, uid, domain)
                if not move_line_ids:
                    continue
            #
            # La regola è ok: ricavo valori all'interno della registrazione
            #
            # Segno
            segno = role.spesometro_segno or False
            # ... Partner e segno(se non impostato)
            partner = False
            domain = [('move_id', '=', move.id)]
            if role.partner_id:
                domain.append(('partner_id', '=', role.partner_id.id))
            else:
                domain.append(('partner_id', '!=', False))
            move_line_ids = move_line_obj.search(cr, uid, domain, order='id')
            if move_line_ids:
                move_line = move_line_obj.browse(cr, uid, move_line_ids[0])
                if role.spesometro_partner_id:
                    partner = role.spesometro_partner_id
                else:
                    partner = move_line.partner_id
                if not segno:
                    if move_line.account_id.type in ['payable']:
                        segno = 'passiva'
                    else:
                        segno = 'attiva'
            # ... Calcolo importo
            res_importo = self.get_importo(cr, uid, role.id, move)
            res = {
                'role_id' : role.id,
                'journal_id': role.journal_id and role.journal_id.id\
                    or False,
                'account_id' : role.account_id and role.account_id.id \
                    or False,
                'counterpart_id' : role.counterpart_id and role.counterpart_id.id \
                    or False,
                'partner_id' : partner and partner.id or False,
                'segno' : segno or False,
                'amount_untaxed': res_importo['amount_untaxed'],
                'amount_tax': res_importo['amount_tax'],
                'amount_total': res_importo['amount_total'],
                'operazione': role.spesometro_operazione,
                'operazione_tipo_importo': role.spesometro_operazione_tipo_importo,
                'tipo_servizio': role.spesometro_tipo_servizio,
                'no_limite_importo': role.no_limite_importo
            }
            break
            
        return res
    

class spesometro_comunicazione(orm.Model):
    
    _name = "spesometro.comunicazione"
    _description = "Spesometro - Comunicazione "
    
    def _tot_operation_number(self, cr, uid, ids, field_names, args, context=None):
        res = {}
        for com in self.browse(cr, uid, ids):
            # Aggregate
            tot_FA = len(com.line_FA_ids)
            tot_SA = len(com.line_SA_ids)
            tot_BL1 = 0
            tot_BL2 = 0
            tot_BL3 = 0
            for line in com.line_BL_ids:
                if line.operazione_fiscalita_privilegiata:
                    tot_BL1 += 1
                elif line.operazione_con_soggetti_non_residenti:
                    tot_BL2 += 1
                elif line.acquisto_servizi_da_soggetti_non_residenti:
                    tot_BL3 += 1
            #Analitiche
            tot_FE = 0 # Fatture emesse
            tot_FE_R = 0 # Doc riepilogativi
            for line in com.line_FE_ids:
                if line.documento_riepilogativo:
                    tot_FE_R += 1
                else:
                    tot_FE += 1
            tot_FR = 0 # Fatture ricevute
            tot_FR_R = 0 # Doc riepilogativi ricevuti
            for line in com.line_FR_ids:
                if line.documento_riepilogativo:
                    tot_FR_R += 1
                else:
                    tot_FR += 1
            tot_NE = len(com.line_NE_ids)
            tot_NR = len(com.line_NR_ids)
            tot_DF = len(com.line_DF_ids)
            tot_FN = len(com.line_FN_ids)
            tot_SE = len(com.line_SE_ids)
            tot_TU = len(com.line_TU_ids)
            
            res[com.id] = {
                    'totale_FA' : tot_FA,
                    'totale_SA' : tot_SA,
                    'totale_BL1' : tot_BL1,
                    'totale_BL2' : tot_BL2,
                    'totale_BL3' : tot_BL3,
                    'totale_FE' : tot_FE,
                    'totale_FE_R' : tot_FE_R,
                    'totale_FR' : tot_FR,
                    'totale_FR_r' : tot_FR_R,
                    'totale_NE' : tot_NE,
                    'totale_NR' : tot_NR,
                    'totale_DF' : tot_DF,
                    'totale_FN' : tot_FN,
                    'totale_SE' : tot_SE,
                    'totale_TU' : tot_TU,
                    }
        return res
    
    _columns = {
        'company_id': fields.many2one('res.company', 'Azienda', required=True ),
        'periodo': fields.selection((('anno','Annuale'), ('trimestre','Trimestrale'), ('mese','Mensile')),
                   'Periodo', required=True),
        'anno' : fields.integer('Anno', size=4, required=True),
        'trimestre' : fields.integer('Trimestre', size=1 ),
        'mese' : fields.selection((('1','Gennaio'), ('2','Febbraio'), ('3','Marzo'), ('4','Aprile'),
                                   ('5','Maggio'), ('6','Giugno'), ('7','Luglio'), ('8','Agosto'),
                                   ('9','Settembre'), ('10','Ottobre'), ('11','Novembre'), ('12','Dicembre'),
                                   ),'Mese'),
        'tipo': fields.selection((('ordinaria','Ordinaria'), ('sostitutiva','Sostitutiva'), ('annullamento','Annullamento')),
                   'Tipo comunicazione', required=True),
        'comunicazione_da_sostituire_annullare': fields.integer('Protocollo comunicaz. da sostituire/annullare'),
        'documento_da_sostituire_annullare': fields.integer('Protocollo documento da sostituire/annullare'),
        
        'formato_dati': fields.selection((('aggregati','Dati Aggregati'), ('analitici','Dati Analitici')),
                   'Formato dati', readonly=True ),
                
        'codice_fornitura': fields.char('Codice fornitura', readonly=True, size=5, help='Impostare a "NSP00" '),
        'tipo_fornitore': fields.selection((('01','Invio propria comunicazione'), ('10','Intermediario')),
                   'Tipo fornitore' ),
        'codice_fiscale_fornitore': fields.char('Codice fiscale Fornitore', size=16, 
                    help="Deve essere uguale al Codice fiscale dell'intermediario (campo 52 del record B) se presente, altrimenti al Codice fiscale del soggetto tenuto alla comunicazione (campo 41 del record B) se presente, altrimenti al Codice fiscale del soggetto obbligato (campo 2 del record B)"),
        #
        # Valori per comunicazione su più invii (non gestito)
        'progressivo_telematico': fields.integer('Progressivo telematico', readonly=True),
        'numero_totale_invii': fields.integer('Numero totale invii telematici', readonly=True),
        #
        # Soggetto a cui si riferisce la comunicazione
        #
        'soggetto_codice_fiscale': fields.char('Codice fiscale soggetto obbligato', size=16, 
                    help="Soggetto cui si riferisce la comunicazione"),
        'soggetto_partitaIVA': fields.char('Partita IVA', size=11),
        'soggetto_codice_attivita': fields.char('Codice attività', size=6, help="Codice ATECO 2007"),
        'soggetto_telefono': fields.char('Telefono', size=12),
        'soggetto_fax': fields.char('Fax', size=12),
        'soggetto_email': fields.char('E-mail', size=50),
        'soggetto_forma_giuridica': fields.selection((('persona_giuridica','Persona Giuridica'), ('persona_fisica','Persona Fisica')),
                   'Forma Giuridica'),
        'soggetto_codice_carica': fields.selection(
                            (('1','Rappresentante legale, negoziale o di fatto, socio amministratore'), 
                             ('2','Rappresentante di minore, inabilitato o interdetto, ovvero curatore dell’eredità giacente, amministratore di eredità devoluta sotto condizione sospensiva o in favore di nascituro non ancora concepito, amministratore di sostegno per le persone con limitata capacità di agire'),
                             ('3','Curatore fallimentare'),
                             ('4','Commissario liquidatore (liquidazione coatta amministrativa ovvero amministrazione straordinaria)'),
                             ('5','Commissario giudiziale (amministrazione controllata) ovvero custode giudiziario (custodia giudiziaria), ovvero amministratore giudiziario in qualità di rappresentante dei beni sequestrati'),
                             ('6','Rappresentante fiscale di soggetto non residente'),
                             ('7','Erede'),
                             ('8','Liquidatore (liquidazione volontaria)'),
                             ('9','Soggetto tenuto a presentare la dichiarazione ai fini IVA per conto del soggetto estinto a seguito di operazioni straordinarie o altre trasformazioni sostanziali soggettive (cessionario d’azienda, società beneficiaria, incorporante, conferitaria, ecc.); ovvero, ai fini delle imposte sui redditi e/o dell’IRAP, rappresentante della società beneficiaria (scissione) o della società risultante dalla fusione o incorporazione'),
                             ('10','Rappresentante fiscale di soggetto non residente con le limitazioni di cui all’art. 44, comma 3, del D.L. n. 331/1993'),
                             ('11','Soggetto esercente l’attività tutoria del minore o interdetto in relazione alla funzione istituzionale rivestita'),
                             ('12','Liquidatore (liquidazione volontaria di ditta individuale - periodo ante messa in liquidazione)'),
                             ),'Codice Carica'),
        
        'soggetto_pf_cognome': fields.char('Cognome', size=24, help=""),
        'soggetto_pf_nome': fields.char('Nome', size=20, help=""),
        'soggetto_pf_sesso': fields.selection((('M','M'), ('F','F')),'Sesso'),
        'soggetto_pf_data_nascita': fields.date('Data di nascita'),
        'soggetto_pf_comune_nascita': fields.char('Comune o stato estero di nascita', size=40),
        'soggetto_pf_provincia_nascita': fields.char('Provincia', size=2),
        'soggetto_pg_denominazione': fields.char('Denominazione', size=60),
        
        # Soggetto tenuto alla comunicazione
        'soggetto_cm_forma_giuridica': fields.selection((('persona_giuridica','Persona Giuridica'), ('persona_fisica','Persona Fisica')),
                   'Forma Giuridica'),
        'soggetto_cm_codice_fiscale': fields.char('Codice Fiscale', size=16, help="Soggetto che effettua la comunicazione se diverso dal soggetto tenuto alla comunicazione"),
        'soggetto_cm_pf_cognome': fields.char('Cognome', size=24, help=""),
        'soggetto_cm_pf_nome': fields.char('Nome', size=20, help=""),
        'soggetto_cm_pf_sesso': fields.selection((('M','M'), ('F','F')),'Sesso'),
        'soggetto_cm_pf_data_nascita': fields.date('Data di nascita'),
        'soggetto_cm_pf_comune_nascita': fields.char('Comune o stato estero di nascita', size=40),
        'soggetto_cm_pf_provincia_nascita': fields.char('Provincia', size=2),
        
        'soggetto_cm_pf_data_inizio_procedura': fields.date('Data inizio procedura'),
        'soggetto_cm_pf_data_fine_procedura': fields.date('Data fine procedura'),
        'soggetto_cm_pg_denominazione': fields.char('Denominazione', size=60),
        
        # Soggetto incaricato alla trasmissione
        'soggetto_trasmissione_codice_fiscale': fields.char('Codice Fiscale', size=16, help="Intermediario che effettua la trasmissione telematica"),
        'soggetto_trasmissione_numero_CAF': fields.integer('Nr iscrizione albo del C.A.F.', size=5, help="Intermediario che effettua la trasmissione telematica"),
        'soggetto_trasmissione_impegno': fields.selection((('1','Soggetto obbligato'), ('2','Intermediario')),'Impegno trasmissione'),
        'soggetto_trasmissione_data_impegno': fields.date('Data data impegno'),
        
        'line_FA_ids': fields.one2many('spesometro.comunicazione.line.fa', 'comunicazione_id', 'Quadri FA' ),
        'line_SA_ids': fields.one2many('spesometro.comunicazione.line.sa', 'comunicazione_id', 'Quadri SA' ),
        'line_BL_ids': fields.one2many('spesometro.comunicazione.line.bl', 'comunicazione_id', 'Quadri BL' ),
        
        'line_FE_ids': fields.one2many('spesometro.comunicazione.line.fe', 'comunicazione_id', 'Quadri FE' ),
        'line_FR_ids': fields.one2many('spesometro.comunicazione.line.fr', 'comunicazione_id', 'Quadri FR' ),
        'line_NE_ids': fields.one2many('spesometro.comunicazione.line.ne', 'comunicazione_id', 'Quadri NE' ),
        'line_NR_ids': fields.one2many('spesometro.comunicazione.line.nr', 'comunicazione_id', 'Quadri NR' ),
        'line_DF_ids': fields.one2many('spesometro.comunicazione.line.df', 'comunicazione_id', 'Quadri DF' ),
        'line_FN_ids': fields.one2many('spesometro.comunicazione.line.fn', 'comunicazione_id', 'Quadri FN' ),
        'line_SE_ids': fields.one2many('spesometro.comunicazione.line.se', 'comunicazione_id', 'Quadri SE' ),
        'line_TU_ids': fields.one2many('spesometro.comunicazione.line.tu', 'comunicazione_id', 'Quadri TU' ),
        
        'totale_FA': fields.function(_tot_operation_number, string='Tot operazioni FA', type='integer', multi='operation_number'),
        'totale_SA': fields.function(_tot_operation_number, string='Tot operazioni SA', type='integer', multi='operation_number'),
        'totale_BL1': fields.function(_tot_operation_number, string='Tot operazioni BL - Paesi con fiscalita privilegiata', type='integer', multi='operation_number'),
        'totale_BL2': fields.function(_tot_operation_number, string='Tot operazioni BL - Soggetti non residenti', type='integer', multi='operation_number'),
        'totale_BL3': fields.function(_tot_operation_number, string='Tot operazioni BL - Acquisti servizi non soggetti non residenti', type='integer', multi='operation_number'),
        
        'totale_FE': fields.function(_tot_operation_number, string='Tot operazioni FE', type='integer', multi='operation_number'),
        'totale_FE_R': fields.function(_tot_operation_number, string='Tot operazioni FE doc riepil.', type='integer', multi='operation_number'),
        'totale_FR': fields.function(_tot_operation_number, string='Tot operazioni FR', type='integer', multi='operation_number'),
        'totale_FR_R': fields.function(_tot_operation_number, string='Tot operazioni FR doc riepil.', type='integer', multi='operation_number'),
        'totale_NE': fields.function(_tot_operation_number, string='Tot operazioni NE', type='integer', multi='operation_number'),
        'totale_NR': fields.function(_tot_operation_number, string='Tot operazioni NR', type='integer', multi='operation_number'),
        'totale_DF': fields.function(_tot_operation_number, string='Tot operazioni DF', type='integer', multi='operation_number'),
        'totale_FN': fields.function(_tot_operation_number, string='Tot operazioni FN', type='integer', multi='operation_number'),
        'totale_SE': fields.function(_tot_operation_number, string='Tot operazioni SE', type='integer', multi='operation_number'),
        'totale_TU': fields.function(_tot_operation_number, string='Tot operazioni TU', type='integer', multi='operation_number'),
    }
    
    _default ={
        'codice_fornitura': 'NSP00',
        'tipo_fornitore': '01',
        'formato_dati': 'aggregati',
    }
    
    def onchange_trasmissione_impegno(self, cr, uid, ids, type, context=None):
        res = {}
        fiscalcode = False
        if type == '1': # soggetto obbligato
            fiscalcode = context.get('soggetto_codice_fiscale', False)
        res = {
               'value' : {'soggetto_trasmissione_codice_fiscale' : fiscalcode}
               }
        return res
    
    def partner_is_from_san_marino(self, cr, uid, move, invoice, arg):
        # configurazione
        anno_competenza = datetime.datetime.strptime(move.period_id.date_start, "%Y-%m-%d").year
        configurazione_ids = self.pool.get('spesometro.configurazione').search(cr, uid, \
                                                       [('anno', '=', anno_competenza)])
        if not configurazione_ids:
            raise orm.except_orm(_('Configurazione mancante!'),_("Configurare l'anno relativo alla comunicazione") )
        configurazione = self.pool.get('spesometro.configurazione').browse(cr, uid, configurazione_ids[0])
        stato_estero = False
        address = self._get_partner_address_obj(cr, uid, move, invoice, arg)
        if address and address.country_id and configurazione.stato_san_marino.id == address.country_id.id:
            return True
        else:
            return False
    
    def _convert_only_number(self, cr, uid, string):
        if not string:
            string = ''
        string = ''.join(e for e in string if e.isdigit())
        return string
    
    def _get_partner_address_obj(self, cr, uid, move, invoice, arg):
        address = False
        partner_address_obj = False
        # Partner
        if 'partner' in arg and arg['partner']:
            partner = arg['partner']
        else:
            partner = move.partner_id
        if partner.parent_id:
            partner_address_obj = partner.parent_id 
        else:
            partner_address_obj = partner
        return partner_address_obj
    
    def compute_amounts(self, cr, uid, move, invoice, arg):
        '''
        Calcolo totali documento. Dall'imponibile vanno esclusi gli importi esclusi, fuori campo o esenti
        '''
        res ={
              'amount_untaxed' : 0,
              'amount_tax' : 0,
              'amount_total' : 0,
              }
        if invoice:
            for line in invoice.tax_line:
                if not line.tax_code_id.spesometro_escludi:
                    res['amount_untaxed'] += line.base
                    res['amount_tax'] += line.amount
                    res['amount_total'] += round(line.base + line.amount, 2)
        else:
            regola = self.pool.get('spesometro.regole').get_regola(cr, uid, 
                                                        move, invoice)
            if regola:
                res['amount_untaxed'] = regola['amount_untaxed']
                res['amount_tax'] = regola['amount_tax']
                res['amount_total'] = regola['amount_total']
            
        return res
            
    def truncate_values(self, cr, uid, ids, context=None):
        for com in self.browse(cr, uid, ids):
            for line in com.line_FA_ids:
                vals = {
                    'attive_imponibile_non_esente': int(line.attive_imponibile_non_esente),
                    'attive_imposta': int(line.attive_imposta),
                    'attive_operazioni_iva_non_esposta': int(line.attive_operazioni_iva_non_esposta),
                    'attive_note_variazione': int(line.attive_note_variazione),
                    'attive_note_variazione_imposta': int(line.attive_note_variazione_imposta),
                
                    'passive_imponibile_non_esente': int(line.passive_imponibile_non_esente),
                    'passive_imposta': int(line.passive_imposta),
                    'passive_operazioni_iva_non_esposta': int(line.passive_operazioni_iva_non_esposta),
                    'passive_note_variazione': int(line.passive_note_variazione),
                    'passive_note_variazione_imposta': int(line.passive_note_variazione_imposta), 
                    }
                self.pool.get('spesometro.comunicazione.line.fa').write(cr, uid, [line.id], vals)
                
            for line in com.line_SA_ids:
                vals = {
                    'importo_complessivo': int(line.importo_complessivo),
                    }
                self.pool.get('spesometro.comunicazione.line.sa').write(cr, uid, [line.id], vals)
                
            for line in com.line_BL_ids:
                vals = {
                    'attive_importo_complessivo': int(line.attive_importo_complessivo),
                    'attive_imposta': int(line.attive_imposta),
                    'attive_non_sogg_cessione_beni': int(line.attive_non_sogg_cessione_beni),
                    'attive_non_sogg_servizi': int(line.attive_non_sogg_servizi),
                    'attive_note_variazione': int(line.attive_note_variazione),
                    'attive_note_variazione_imposta': int(line.attive_note_variazione_imposta),
                
                    'passive_importo_complessivo': int(line.passive_importo_complessivo),
                    'passive_imposta': int(line.passive_imposta),
                    'passive_non_sogg_importo_complessivo': int(line.passive_non_sogg_importo_complessivo),
                    'passive_note_variazione': int(line.passive_note_variazione),
                    'passive_note_variazione_imposta': int(line.passive_note_variazione_imposta), 
                    }
                self.pool.get('spesometro.comunicazione.line.bl').write(cr, uid, [line.id], vals)
                
        return True
    
    def validate_lines(self, cr, uid, ids, context=None):
        for com in self.browse(cr, uid, ids):
            
            # configurazione
            configurazione_ids = self.pool.get('spesometro.configurazione').search(cr, uid, \
                                                            [('anno', '=', com.anno)])
            if not configurazione_ids:
                raise orm.except_orm(_('Configurazione mancante!'),_("Configurare l'anno relativo alla comunicazione") )
            configurazione = self.pool.get('spesometro.configurazione').browse(cr, uid, configurazione_ids[0])
            
            for line in com.line_FA_ids:
                # Converto saldi negativi x casi di importi estrapolati dalla contabilità
                if line.attive_imponibile_non_esente< 0:
                    importo_positivo = line.attive_imponibile_non_esente * -1 
                    self.pool.get('spesometro.comunicazione.line.fa').write(
                            cr, uid,
                            line.id, 
                            {'attive_imponibile_non_esente':importo_positivo}
                            )
                if configurazione.quadro_fa_limite_importo :
                    if line.attive_imponibile_non_esente and \
                        line.attive_imponibile_non_esente < configurazione.quadro_fa_limite_importo:
                        self.pool.get('spesometro.comunicazione.line.fa').unlink(cr, uid, [line.id])    
            
            for line in com.line_SA_ids:
                # Converto saldi negativi x casi di importi estrapolati dalla contabilità
                if line.importo_complessivo< 0:
                    importo_positivo = line.importo_complessivo * -1 
                    self.pool.get('spesometro.comunicazione.line.sa').write(
                            cr, uid,
                            line.id, 
                            {'importo_complessivo':importo_positivo}
                            )
                if configurazione.quadro_sa_limite_importo :
                    if line.importo_complessivo and \
                        line.importo_complessivo < configurazione.quadro_sa_limite_importo:            
                        self.pool.get('spesometro.comunicazione.line.sa').unlink(cr, uid, [line.id])
            
            for line in com.line_BL_ids:
                #'operazione_fiscalita_privilegiata': fields.boolean('Operazione con pesei con fiscalità privilegiata'), 
                #'operazione_con_soggetti_non_residenti': fields.boolean('Operazione con soggetto non residente'), 
                #'acquisto_servizi_da_soggetti_non_residenti': fields.boolean('Acquisto di servizi da soggetti non residenti'), 
                
                importo_test = 0
                # operazioni attive
                if line.attive_importo_complessivo :
                    importo_test = line.attive_importo_complessivo
                elif line.attive_non_sogg_cessione_beni :
                    importo_test = line.attive_non_sogg_cessione_beni
                elif line.attive_non_sogg_servizi :
                    importo_test = line.attive_non_sogg_servizi
                # operazioni passive
                elif line.passive_importo_complessivo :
                    importo_test = line.passive_importo_complessivo
                elif line.passive_non_sogg_importo_complessivo :
                    importo_test = line.passive_non_sogg_importo_complessivo
                
                to_remove = False
                # BL1 - Operazione con pesei con fiscalità privilegiata
                if line.operazione_fiscalita_privilegiata\
                        and configurazione.quadro_bl1_limite_importo :
                    if importo_test < configurazione.quadro_bl1_limite_importo: 
                        to_remove = True
                # BL2 - Operazione con soggetto non residente
                if line.operazione_con_soggetti_non_residenti\
                        and configurazione.quadro_bl2_limite_importo :
                    if importo_test < configurazione.quadro_bl2_limite_importo: 
                        to_remove = True        
                # BL3 - Acquisto di servizi da soggetti non residenti
                if line.acquisto_servizi_da_soggetti_non_residenti\
                        and configurazione.quadro_bl3_limite_importo :
                    if importo_test < configurazione.quadro_bl3_limite_importo: 
                        to_remove = True        
                            
                if to_remove:
                    self.pool.get('spesometro.comunicazione.line.bl').unlink(\
                                                            cr, uid, [line.id])
            
            # Controllo formale comunicazione
            # ... periodo in presenza di linee nel quadro SE
            if com.line_SE_ids and not com.trimestre and not com.mese:
                raise orm.except_orm(_('Perido Errato!'),_("In presenza di operazione nel qudro SE (Acquisti da San Marino) \
                        sono ammessi solo periodi mensili/trimestrali") )
        
        return True
    
    def validate_operation(self, cr, uid, move, invoice, arg):
            # configurazione
            anno_competenza = datetime.datetime.strptime(move.period_id.date_start, "%Y-%m-%d").year
            configurazione_ids = self.pool.get('spesometro.configurazione').search(cr, uid, \
                                                           [('anno', '=', anno_competenza)])
            if not configurazione_ids:
                raise orm.except_orm(_('Configurazione mancante!'),_("Configurare l'anno relativo alla comunicazione") )
            configurazione = self.pool.get('spesometro.configurazione').browse(cr, uid, configurazione_ids[0])
            
            doc_vals = self.pool.get('spesometro.comunicazione').compute_amounts(cr, uid, move, invoice, arg)
            
            # Nessu quadro definito
            if not arg['quadro']:
                return False
            # Quadro richiesto
            if arg['quadro'] not in arg['quadri_richiesti']:
                return False
            # Valori minimi
            # ... valori assoluti x confronti
            amount_total = doc_vals.get('amount_total', 0)
            if amount_total < 0:
                amount_total = amount_total * -1
            amount_untaxed = doc_vals.get('amount_untaxed', 0)
            if amount_untaxed < 0:
                amount_untaxed = amount_untaxed * -1
                
            # Nessun valore
            if not amount_total and not amount_untaxed:
                return False
            # Limiti
            if not arg['no_limite_importo']:
                if arg['quadro'] == 'FA':
                    if configurazione.quadro_fa_limite_importo_line :
                        if not amount_untaxed or amount_untaxed < configurazione.quadro_fa_limite_importo_line:  
                            return False
                if arg['quadro'] == 'SA':
                    if configurazione.quadro_sa_limite_importo_line :
                        if not amount_total or amount_total < configurazione.quadro_sa_limite_importo_line:  
                            return False
                if arg['quadro'] == 'BL':
                    if arg['operazione'] == 'BL1':
                        if configurazione.quadro_bl1_limite_importo_line :
                            if not amount_total \
                                or amount_total < configurazione.quadro_bl1_limite_importo_line: 
                                return False
                    if arg['operazione'] == 'BL2':
                        if configurazione.quadro_bl2_limite_importo_line :
                            if not amount_total \
                                or amount_total < configurazione.quadro_bl2_limite_importo_line: 
                                return False
                    if arg['operazione'] == 'BL3':
                        if configurazione.quadro_bl3_limite_importo_line :
                            if not amount_total \
                                or amount_total < configurazione.quadro_bl3_limite_importo_line: 
                                return False
                
                if arg['quadro'] == 'SE':
                    if configurazione.quadro_se_limite_importo_line :
                        if not amount_untaxed or amount_untaxed < configurazione.quadro_se_limite_importo_line: 
                            return False
            
            # Operazioni con San Marino Escluse se richiesta forma aggregata
            if arg['formato_dati'] == 'aggregati' and self.partner_is_from_san_marino(cr, uid, move, invoice, arg):
                return False
            
            return True
    
    def get_define_quadro(self, cr, uid, move, invoice, arg):
        
        quadro = False
        operazione = arg.get('operazione')
        # Forma aggregata
        if arg['formato_dati'] == 'aggregati':
            if operazione == 'FA' or operazione == 'DR':
                quadro = 'FA'
            elif operazione == 'SA': # Operazioni senza fattura
                quadro = 'SA'
            elif operazione in ['BL1', 'BL2', 'BL3']:
                quadro = 'BL'
        
        # Forma analitica
        if arg['formato_dati'] == 'analitici':
            
            # Priorità x San Marino -> quadro SE
            if self.partner_is_from_san_marino(cr, uid, move, invoice, arg):
                operazione = 'BL3'
            
            # Impostazioni anagrafiche partner
            if operazione == 'FA' or operazione == 'DR':
                if arg.get('segno') == 'attiva':
                    quadro = 'FE'
                elif arg.get('segno') == 'passiva':
                    quadro = 'FR'
            elif operazione == 'SA': # Operazioni senza fattura
                quadro = 'DF'
            elif operazione == 'BL2': #Operazioni con soggetti non residenti
                quadro = 'FN'
            elif operazione == 'BL1' or operazione == 'BL3': #Operazioni con paesi con fiscalità privilegiata - Acquisti di servizi da soggetti non residenti
                quadro = 'SE'
            # Note di variazione
            if operazione == 'FE' and 'refund' in move.journal_id.type:
                operazione = 'NE'
            elif operazione == 'FR' and 'refund' in move.journal_id.type:
                operazione = 'NR'
        
        return quadro
    
    
    def genera_comunicazione(self, cr, uid, params, context=None):
        
        def _get_periods(cr, uid, params, context=None):
            '''
            Definizione periodi di competenza
            '''
            sql_select = "SELECT p.id FROM account_period p "
            sql_where = " WHERE p.special = False "
            search_params = {}
            # Periodo annuale
            if params.get('periodo') == 'anno':
                period_date_start = datetime.date(params.get('anno') , 1, 1)
                period_date_stop = datetime.date(params.get('anno') , 12, 31)
                sql_where += " AND p.date_start >= date(%(period_date_start)s) AND p.date_stop <=date(%(period_date_stop)s) "
                search_params.update({
                        'period_date_start' : period_date_start,
                        'period_date_stop' : period_date_stop
                         })
            # Periodo mensile
            if params.get('periodo') == 'mese':
                period_date_start = datetime.date(params.get('anno') , int(params.get('mese')), 1)
                sql_where += " AND p.date_start = date(%(period_date_start)s) "
                search_params.update({
                        'period_date_start' : period_date_start,
                         })
            # Periodo trimestrale
            if params.get('periodo') == 'trimestre':
                if params.get('trimestre') == 1:
                    period_date_start = datetime.date(params.get('anno') , 1, 1)
                    period_date_stop = datetime.date(params.get('anno') , 3, 31)
                elif params.get('trimestre') == 2:
                    period_date_start = datetime.date(params.get('anno') , 3, 1)
                    period_date_stop = datetime.date(params.get('anno') , 6, 30)
                elif params.get('trimestre') == 2:
                    period_date_start = datetime.date(params.get('anno') , 7, 1)
                    period_date_stop = datetime.date(params.get('anno') , 9, 30)
                elif params.get('trimestre') == 2:
                    period_date_start = datetime.date(params.get('anno') , 10, 1)
                    period_date_stop = datetime.date(params.get('anno') , 12, 31)
                else:
                    raise orm.except_orm(_('Dato errato!'),_("Errore nel valore del trimestre") )
                sql_where += " AND p.date_start >= date(%(period_date_start)s) AND p.date_stop <=date(%(period_date_stop)s) "
                search_params.update({
                        'period_date_start' : period_date_start,
                        'period_date_stop' : period_date_stop
                         })
                
            sql = sql_select + sql_where
            cr.execute(sql, search_params)
            periods =  [i[0] for i in cr.fetchall()]
            return periods
            
        def _genera_testata(cr, uid, params, context=None):
            '''
            Generazione testata dichiarazione
            '''
            company = self.pool.get('res.company').browse(cr, uid, params['company_id'])
            # progressivo telematico :" il progressivo deve essere univoco e crescente (con incrementi di una unità per ogni file prodotto)"
            if params['tipo'] == 'ordinaria':
                com_search = [('tipo', '=', 'ordinaria')]
                com_last_ids = self.search(cr, uid, com_search, order='progressivo_telematico desc', limit=1)
                com_next_prg = 1
                if com_last_ids:
                    com_next_prg = self.browse(cr, uid, com_last_ids[0]).progressivo_telematico + 1
            progressivo_telematico = com_next_prg
            # vat
            if company.partner_id.vat:
                partita_iva = company.partner_id.vat[2:]
            else:
                partita_iva = '{:11s}'.format("".zfill(11))
            # codice fiscale soggetto incaricato alla trasmissione
            codice_fiscale_incaricato_trasmissione=''
            if  params.get('tipo_fornitore') == '10' and params.get('partner_intermediario', False):
                partner_intermediario = self.pool.get('res.partner').browse(cr, uid, params.get('partner_intermediario'))
                codice_fiscale_incaricato_trasmissione = partner_intermediario.fiscalcode or False
            # Soggetto con impegno alla trasmissione
            if  params.get('tipo_fornitore') == '10':
                soggetto_trasmissione_impegno = '2'
            else:
                soggetto_trasmissione_impegno = '1'
            # Persona fisica o giuridica
            # Considerazione: se se lunghezza codice fiscale < 16 allora c'è la P.Iva e quindi trattasi di soggetto giuridico
            tipo_persona = 'persona_fisica'
            if company.partner_id.fiscalcode and len(company.partner_id.fiscalcode) < 16:
                tipo_persona = 'persona_giuridica'
                
            values = {
                      'company_id' : company.id,
                      'codice_fiscale_fornitore' : company.partner_id.fiscalcode,
                      'tipo' : params.get('tipo', False),
                      'periodo' : params.get('periodo', False),
                      'anno' : params.get('anno', False),
                      'mese' : params.get('mese', False),
                      'trimestre' : params.get('trimestre', False),
                      'progressivo_telematico' : progressivo_telematico or False,
                      'tipo_fornitore' : params.get('tipo_fornitore', False),
                      'formato_dati' : params.get('formato_dati', False),
                      'soggetto_codice_fiscale' : company.partner_id and company.partner_id.fiscalcode or '',  
                      'soggetto_partitaIVA' : partita_iva,
                      'soggetto_telefono' : company.partner_id and company.partner_id.phone or '',  
                      'soggetto_fax' : company.partner_id and company.partner_id.fax or '',  
                      'soggetto_email' : company.partner_id and company.partner_id.email or '',
                      'soggetto_forma_giuridica' : tipo_persona,  
                      'soggetto_pg_denominazione' : company.partner_id and company.partner_id.name or company.name or '',
                      'soggetto_cm_forma_giuridica' : tipo_persona,  
                      'soggetto_cm_pg_denominazione' : company.partner_id and company.partner_id.name or company.name or '',
                      'soggetto_trasmissione_codice_fiscale' : codice_fiscale_incaricato_trasmissione,  
                      'soggetto_trasmissione_impegno' : soggetto_trasmissione_impegno,  
                      }
            # Pulizia caratteri speciali
            if values['soggetto_telefono']:
                values['soggetto_telefono'] = self._convert_only_number(
                                                cr, uid, values['soggetto_telefono']) 
            if values['soggetto_fax']:
                values['soggetto_fax'] = self._convert_only_number(
                                                cr, uid, values['soggetto_fax']) 
                
            comunicazione_id = self.create(cr, uid, values)
            
            return comunicazione_id
        
        
        # Esistenza record di configurazione per l'anno della comunicazione
        configurazione_ids = self.pool.get('spesometro.configurazione').search(cr, uid, [('anno', '=', params.get('anno'))])
        if not configurazione_ids:
            raise orm.except_orm(_('Configurazione mancante!'),_("Configurare l'anno relativo alla comunicazione") )
        configurazione = self.pool.get('spesometro.configurazione').browse(cr, uid, configurazione_ids[0])
        
        # Testata comunicazione
        comunicazione_id = _genera_testata(cr, uid, params, context=None)
        
        period_obj = self.pool.get('account.period')
        journal_obj = self.pool.get('account.journal')
        partner_obj = self.pool.get('res.partner')
        account_move_obj = self.pool.get('account.move')
        account_move_line_obj = self.pool.get('account.move.line')
        invoice_obj = self.pool.get('account.invoice')
        # periods
        period_ids = _get_periods(cr, uid, params, context=None)
        # journal
        journal_search = [('spesometro','=', True)]
        journal_ids = journal_obj.search(cr, uid, journal_search, context=context)
        # Partners to exclude
        partner_search = [('spesometro_escludi','=', True)]
        partner_to_exclude_ids = partner_obj.search(cr, uid, partner_search, context=context)
        
        move_search = [('company_id', '=', params['company_id']),
                       ('period_id','in', period_ids), 
                       #('journal_id','in', journal_ids), selezione fatta da regole 
                       ('partner_id','not in', partner_to_exclude_ids)]
        #move_search.append(('partner_id','=', 4155))
        move_ids = account_move_obj.search(cr, uid, move_search, context=context)
        
        for move in self.pool.get('account.move').browse(cr, uid, move_ids):
            # Test move validate
            # ...evito di leggere tutti i movimenti se non sono impostate regole
            #    che possono prendere in considerazione movimenti senza partner
            if not configurazione.regole_ids \
                    and not move.partner_id:
                continue
            print "spesometro move > > " + str(move.id)
            
            # Invoice
            invoice = False
            invoice_search = [('move_id','=', move.id)]
            invoice_ids = invoice_obj.search(cr, uid, invoice_search, context=context)
            if invoice_ids:
                invoice = invoice_obj.browse(cr,uid, invoice_ids[0])
            # Partner
            partner = False
            if invoice:
                partner = invoice.partner_id
            elif move.partner_id:
                partner = move.partner_id
            else:
                domain =[('partner_id', '!=', False)]
                ml_ids = account_move_line_obj.search(cr, uid, domain)
                if ml_ids:
                    line = account_move_line_obj.browse(cr, uid, ml_ids[0])
                    partner = line.partner_id
            
            # Config spesometro
            operazione = False
            operazione_tipo_importo = False
            tipo_servizio = False
            no_limite_importo = False
            operazione_iva_non_esposta = False
            operazione = move.journal_id.spesometro_operazione
            operazione_iva_non_esposta = move.journal_id.spesometro_IVA_non_esposta
            segno = move.journal_id.spesometro_segno
            
            # Config spesometro - Da regole
            regola = self.pool.get('spesometro.regole').get_regola(cr, uid, 
                                                        move, invoice)
            if regola:
                if regola.get('operazione'):
                    operazione = regola.get('operazione')
                if regola.get('operazione_tipo_importo'):
                    operazione_tipo_importo = regola.get('operazione_tipo_importo')
                if regola.get('tipo_servizio'):
                    tipo_servizio = regola.get('tipo_servizio')
                if regola.get('segno'):
                    segno = regola.get('segno')
                if regola.get('partner_id'):
                    partner = partner_obj.browse(cr, uid, regola['partner_id'])
                if regola.get('no_limite_importo'):
                    no_limite_importo = regola.get('no_limite_importo')
            
            # Salto movimento se:
            #   - Nessuna regola valida 
            #   - La fattura appartiene ad un sezionale dove la comunicaz.art.21 non è configurata
            if invoice and not invoice.journal_id.id in journal_ids:
                continue
            if not invoice and not regola:
                continue
            
            if invoice:
                print 'INVOICE' + invoice.number
                
            
            # Config partner -> priorità alle impostazioni del partner
            if partner.spesometro_operazione:
                operazione = partner.spesometro_operazione
                operazione_tipo_importo = partner.spesometro_operazione_tipo_importo
                tipo_servizio = partner.spesometro_tipo_servizio 
                operazione_iva_non_esposta = partner.spesometro_IVA_non_esposta
            
            arg = {
                'comunicazione_id' : comunicazione_id,   
                'partner' : partner,   
                'segno' : segno,   
                'operazione_iva_non_esposta' : operazione_iva_non_esposta,
                'operazione' : operazione,
                'operazione_tipo_importo' : operazione_tipo_importo,
                'tipo_servizio' : tipo_servizio,
                'no_limite_importo' : no_limite_importo,
                'formato_dati' : params['formato_dati'],
                'quadri_richiesti' : params['quadri_richiesti'],
                }
            
            # Quadro di competenza
            quadro = self.get_define_quadro(cr, uid, move, invoice, arg)
            
            arg.update({'quadro': quadro})
            
            # Test operazione da includere nella comunicazione
            if not self.validate_operation(cr, uid, move, invoice, arg):
                continue
            
            if quadro == 'FA':
                line_id = self.pool.get('spesometro.comunicazione.line.fa').add_line(cr, uid, move, invoice, arg)
            if quadro == 'SA':
                line_id = self.pool.get('spesometro.comunicazione.line.sa').add_line(cr, uid, move, invoice, arg)
            if quadro == 'BL':
                line_id = self.pool.get('spesometro.comunicazione.line.bl').add_line(cr, uid, move, invoice, arg)
            if quadro == 'SE':
                line_id = self.pool.get('spesometro.comunicazione.line.se').add_line(cr, uid, move, invoice, arg)
        
        # Arrotonda importi su valori raggruppati -> troncare i decimali
        if params['formato_dati'] == 'aggregati':
            self.truncate_values(cr, uid, [comunicazione_id])
            
        # Rimuove le linee che non rientrano nei limiti ed effettua un controllo formale sull'intera comunicazione
        self.validate_lines(cr, uid, [comunicazione_id])
        
        # Update for compute totals
        self.write(cr, uid, [comunicazione_id],{})
        
        return True
    

class spesometro_comunicazione_line_FA(orm.Model):
    '''
    QUADRO FA - Operazioni documentate da fattura esposte in forma aggregata
    '''

    _name = "spesometro.comunicazione.line.fa"
    _description = "Spesometro - Comunicazione linee quadro FA"
    _columns = {
        'comunicazione_id': fields.many2one('spesometro.comunicazione', 'Comunicazione', ondelete='cascade'),
        
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'partita_iva': fields.char('Partita IVA', size=11),
        'codice_fiscale': fields.char('Codice Fiscale', size=16),
        'documento_riepilogativo': fields.boolean('Documento Riepilogativo'),
        'noleggio': fields.selection((('A','Autovettura'), ('B','Caravan'), ('C','Altri Veicoli'), ('D','Unità  da diporto'), ('E','Aeromobii')),'Leasing'),
        
        'numero_operazioni_attive_aggregate': fields.integer('Nr op. attive', size=16),
        'numero_operazioni_passive_aggregate': fields.integer('Nr op. passive', size=16),
        
        'attive_imponibile_non_esente': fields.float('Tot impon., non impon ed esenti', digits_compute=dp.get_precision('Account'), help="Totale operazioni imponibili, non imponibili ed esenti"),
        'attive_imposta': fields.float(' Tot imposta', digits_compute=dp.get_precision('Account'), help="Totale imposta"),
        'attive_operazioni_iva_non_esposta': fields.float('Totale operaz. IVA non esposta', digits_compute=dp.get_precision('Account'), help="Totale operazioni con IVA non esposta"),
        'attive_note_variazione': fields.float('Totale note variazione', digits_compute=dp.get_precision('Account'), help="Totale note di variazione a debito per la controparte"),
        'attive_note_variazione_imposta': fields.float('Totale imposta note variazione', digits_compute=dp.get_precision('Account'), help="Totale imposta sulle note di variazione a debito"),
        
        'passive_imponibile_non_esente': fields.float('Tot impon., non impon ed esenti', digits_compute=dp.get_precision('Account'), help="Totale operazioni imponibili, non imponibili ed esenti"),
        'passive_imposta': fields.float('Totale imposta', digits_compute=dp.get_precision('Account'), help="Totale imposta"),
        'passive_operazioni_iva_non_esposta': fields.float('Totale operaz. IVA non esposta', digits_compute=dp.get_precision('Account'), help="Totale operazioni con IVA non esposta"),
        'passive_note_variazione': fields.float('Totale note variazione', digits_compute=dp.get_precision('Account'), help="Totale note di variazione a credito per la controparte"),
        'passive_note_variazione_imposta': fields.float('Totale imposta note variazione', digits_compute=dp.get_precision('Account'), help="Totale imposta sulle note di variazione a credito"),
        }
    
    
    def add_line(self, cr, uid, move, invoice, arg):
        comunicazione_lines_obj = self.pool.get('spesometro.comunicazione.line.fa')
        # Partner
        if 'partner' in arg and arg['partner']:
            partner = arg['partner']
        else:
            partner = move.partner_id
        # Comunicazione
        comunicazione_id = arg.get('comunicazione_id', False)
        com_line_search = [('comunicazione_id','=',comunicazione_id), ('partner_id', '=', partner.id)]
        com_line_ids = self.search(cr, uid, com_line_search)
        # Valori documento
        #if invoice :
        #    print invoice.number
        #    import pdb
        #    pdb.set_trace()
        val = {}
        doc_vals = self.pool.get('spesometro.comunicazione').compute_amounts(cr, uid, move, invoice, arg)
        # New partner
        if not com_line_ids:
            partita_iva =''
            if partner.vat:
                partita_iva = partner.vat[2:]
            documento_riepilogativo = False
            if arg['operazione'] == 'DR':
                documento_riepilogativo = True
            val = {
                'comunicazione_id' : comunicazione_id,
                'partner_id' : partner.id,
                'partita_iva' : partita_iva,
                'codice_fiscale' : partner.fiscalcode or '',
                'noleggio' : partner.spesometro_leasing or '',
                'documento_riepilogativo' : documento_riepilogativo,
                }
            # attive
            if arg.get('segno', False) == 'attiva':
                val['numero_operazioni_attive_aggregate'] = 1
                if 'refund' in move.journal_id.type:
                    val['attive_note_variazione'] = doc_vals.get('amount_untaxed', 0)
                    val['attive_note_variazione_imposta'] = doc_vals.get('amount_tax', 0)
                else:
                    if arg.get('operazione_iva_non_esposta', False):
                        val['attive_operazioni_iva_non_esposta' ] = doc_vals.get('amount_total', 0) 
                    else:
                        val['attive_imponibile_non_esente' ] = doc_vals.get('amount_untaxed', 0)
                        val['attive_imposta'] =doc_vals.get('amount_tax', 0)
            # passive         
            else:
                val['numero_operazioni_passive_aggregate'] = 1
                if 'refund' in move.journal_id.type:
                    val['passive_note_variazione'] = doc_vals.get('amount_untaxed', 0)
                    val['passive_note_variazione_imposta'] = doc_vals.get('amount_tax', 0)
                else:
                    if arg.get('operazione_iva_non_esposta', False):
                        val['passive_operazioni_iva_non_esposta' ] = doc_vals.get('amount_total', 0) 
                    else:
                        val['passive_imponibile_non_esente' ] = doc_vals.get('amount_untaxed', 0)
                        val['passive_imposta' ] = doc_vals.get('amount_tax', 0)
            
        # Partner already exists
        if com_line_ids:
            for com_line in self.browse(cr, uid, com_line_ids):
                # attive
                if arg.get('segno', False) == 'attiva':
                    val['numero_operazioni_attive_aggregate'] = com_line.numero_operazioni_attive_aggregate + 1
                    if 'refund' in move.journal_id.type:
                        val['attive_note_variazione'] = com_line.attive_note_variazione + doc_vals.get('amount_untaxed', 0)
                        val['attive_note_variazione_imposta'] = com_line.attive_note_variazione_imposta + doc_vals.get('amount_tax', 0)
                    else:
                        if arg.get('operazione_iva_non_esposta', False):
                            val['attive_operazioni_iva_non_esposta' ] = com_line.attive_operazioni_iva_non_esposta + doc_vals.get('amount_total', 0)
                        else:
                            val['attive_imponibile_non_esente' ] = com_line.attive_imponibile_non_esente + doc_vals.get('amount_untaxed', 0)
                            val['attive_imposta' ] = com_line.attive_imposta + doc_vals.get('amount_tax', 0)
                # passive         
                else:
                    val['numero_operazioni_passive_aggregate'] = com_line.numero_operazioni_passive_aggregate + 1
                    if 'refund' in move.journal_id.type:
                        val['passive_note_variazione'] = com_line.passive_note_variazione + doc_vals.get('amount_untaxed', 0)
                        val['passive_note_variazione_imposta'] = com_line.passive_note_variazione_imposta + doc_vals.get('amount_tax', 0)
                    else:
                        if arg.get('operazione_iva_non_esposta', False):
                            val['passive_operazioni_iva_non_esposta' ] = com_line.passive_operazioni_iva_non_esposta + doc_vals.get('amount_total', 0) 
                        else:
                            val['passive_imponibile_non_esente' ] = com_line.passive_imponibile_non_esente + doc_vals.get('amount_untaxed', 0)
                            val['passive_imposta' ] = com_line.passive_imposta + doc_vals.get('amount_tax', 0)
            
        if com_line_ids:
            line_id = com_line.id
            self.write(cr, uid, [com_line.id], val)
        else:
            line_id = self.create(cr, uid, val)
        
        return line_id

class spesometro_comunicazione_line_SA(orm.Model):
    '''
    QUADRO SA - Operazioni senza fattura esposte in forma aggregata
    '''
    _name = "spesometro.comunicazione.line.sa"
    _description = "Spesometro - Comunicazione linee quadro SA"
    _columns = {
        'comunicazione_id': fields.many2one('spesometro.comunicazione', 'Comunicazione' , ondelete='cascade'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'codice_fiscale': fields.char('Codice Fiscale', size=16),
        
        'numero_operazioni': fields.integer('Numero operazioni'),
        'importo_complessivo': fields.float('Importo complessivo', digits_compute=dp.get_precision('Account')),
        'noleggio': fields.selection((('A','Autovettura'), ('B','Caravan'), ('C','Altri Veicoli'), ('D','Unità  da diporto'), ('E','Aeromobii')),'Leasing'),
        }
    
    def add_line(self, cr, uid, move, invoice, arg):
        # Partner
        if 'partner' in arg and arg['partner']:
            partner = arg['partner']
        else:
            partner = move.partner_id
        # Comunicazione
        comunicazione_id = arg.get('comunicazione_id', False)
        com_line_search = [('comunicazione_id','=',comunicazione_id), ('partner_id', '=', partner.id)]
        com_line_ids = self.search(cr, uid, com_line_search)
        # Valori documento
        val = {}
        doc_vals = self.pool.get('spesometro.comunicazione').compute_amounts(cr, uid, move, invoice, arg)
        # New partner
        if not com_line_ids:
            val = {
                'comunicazione_id' : comunicazione_id,
                'partner_id' : partner.id,
                'codice_fiscale' : partner.fiscalcode or False,
                'noleggio' : partner.spesometro_leasing or False,
                'numero_operazioni' : 1,
                'importo_complessivo' : doc_vals.get('amount_total', 0),
                }
        # Partner already exists
        if com_line_ids:
            for com_line in self.browse(cr, uid, com_line_ids):
                val['numero_operazioni'] = com_line.numero_operazioni + 1
                val['importo_complessivo'] = com_line.importo_complessivo + doc_vals.get('amount_total', 0)
            
        if com_line_ids:
            line_id = com_line.id
            self.write(cr, uid, [com_line.id], val)
        else:
            line_id = self.create(cr, uid, val)
        
        return line_id

class spesometro_comunicazione_line_BL(orm.Model):
    '''
    QUADRO BL
    - Operazioni con paesi con fiscalità privilegiata (è obbligatorio compilare le sezioni BL001, BL002
         e almeno un campo delle sezioni BL003, BL004, BL005, BL006, BL007, BL008)
    - Operazioni con soggetti non residenti (è obbligatorio compilare le sezioni BL001, BL002 e almeno 
        un campo delle sezioni BL003 e BL006)
    - Acquisti di servizi da soggetti non residenti (è obbligatorio compilare le sezioni BL001, BL002 e 
    almeno un campo della sezione BL006)
    '''
    _name = "spesometro.comunicazione.line.bl"
    _description = "Spesometro - Comunicazione linee quadro BL"
    _columns = {
        'comunicazione_id': fields.many2one('spesometro.comunicazione', 'Comunicazione', ondelete='cascade'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'codice_fiscale': fields.char('Codice Fiscale', size=16),
        
        'numero_operazioni': fields.integer('Numero operazioni'),
        'importo_complessivo': fields.integer('Importo complessivo', digits_compute=dp.get_precision('Account')),
        'noleggio': fields.selection((('A','Autovettura'), ('B','Caravan'), ('C','Altri Veicoli'), ('D','Unità  da diporto'), ('E','Aeromobii')),'Leasing'),
        
        'pf_cognome': fields.char('Cognome', size=24, help=""),
        'pf_nome': fields.char('Nome', size=20, help=""),
        'pf_data_nascita': fields.date('Data di nascita'),
        'pf_comune_stato_nascita': fields.char('Comune o stato estero di nascita', size=40),
        'pf_provincia_nascita': fields.char('Provincia', size=2),
        'pf_codice_stato_estero': fields.char('Codice Stato Estero', size=3, help="Deve essere uno di quelli presenti nella tabella 'elenco dei paesi e\
                    territori esteri' pubblicata nelle istruzioni del modello Unico"),
        'pg_denominazione': fields.char('Denominazione/Ragione sociale', size=60),
        'pg_citta_estera_sede_legale': fields.char('Città estera delle Sede legale', size=40),
        'pg_codice_stato_estero': fields.char('Codice Stato Estero', size=3, help="Deve essere uno di quelli presenti nella tabella 'elenco dei paesi e\
                    territori esteri' pubblicata nelle istruzioni del modello Unico"),
        'pg_indirizzo_sede_legale': fields.char('Indirizzo sede legale', size=60),
         
        'codice_identificativo_IVA': fields.char('Codice identificativo IVA', size=16), 
        'operazione_fiscalita_privilegiata': fields.boolean('Operazione con pesei con fiscalità privilegiata'), 
        'operazione_con_soggetti_non_residenti': fields.boolean('Operazione con soggetto non residente'), 
        'acquisto_servizi_da_soggetti_non_residenti': fields.boolean('Acquisto di servizi da soggetti non residenti'), 
        'operazione_tipo_importo': fields.selection((
                        ('INE','Imponibile, Non Imponibile, Esente'), 
                        ('NS','Non Soggette ad IVA'),
                        ('NV','Note di variazione')),
                   'Tipo Importo' ),
        
        'attive_importo_complessivo': fields.float('Tot operaz. attive impon., non impon ed esenti', digits_compute=dp.get_precision('Account'), help="Totale operazioni imponibili, non imponibili ed esenti"),
        'attive_imposta': fields.float('Tot operaz. attive imposta', digits_compute=dp.get_precision('Account'), help="Totale imposta"),
        'attive_non_sogg_cessione_beni': fields.float('Operaz.attive non soggette ad IVA - Cessione beni', digits_compute=dp.get_precision('Account'), help="Totale operazioni imponibili, non imponibili ed esenti"),
        'attive_non_sogg_servizi': fields.float('Operaz.attive non soggette ad IVA - Servizi', digits_compute=dp.get_precision('Account'), help="Totale operazioni imponibili, non imponibili ed esenti"),
        'attive_note_variazione': fields.float('Totale note variazione', digits_compute=dp.get_precision('Account'), help="Totale note di variazione a debito per la controparte"),
        'attive_note_variazione_imposta': fields.float('Totale imposta note variazione', digits_compute=dp.get_precision('Account'), help="Totale imposta sulle note di variazione a debito"),
        
        'passive_importo_complessivo': fields.float('Tot operaz. passive impon., non impon ed esenti', digits_compute=dp.get_precision('Account'), help="Totale operazioni imponibili, non imponibili ed esenti"),
        'passive_imposta': fields.float('Tot operaz. passive imposta', digits_compute=dp.get_precision('Account'), help="Totale imposta"),
        'passive_non_sogg_importo_complessivo': fields.float('Operaz.passive non soggette ad IVA', digits_compute=dp.get_precision('Account'), help="Totale operazioni imponibili, non imponibili ed esenti"),
        'passive_note_variazione': fields.float('Totale note variazione', digits_compute=dp.get_precision('Account'), help="Totale note di variazione a debito per la controparte"),
        'passive_note_variazione_imposta': fields.float('Totale imposta note variazione', digits_compute=dp.get_precision('Account'), help="Totale imposta sulle note di variazione a debito"),
        
        }
    
    def add_line(self, cr, uid, move, invoice, arg):
        comunicazione_lines_obj = self.pool.get('spesometro.comunicazione.line.bl')
        # Partner
        if 'partner' in arg and arg['partner']:
            partner = arg['partner']
        else:
            partner = move.partner_id
        # Operazione 
        operazione = arg.get('operazione')
        # Operazione tipo importo
        operazione_tipo_importo = arg.get('operazione_tipo_importo')
        # Tipo servizio
        tipo_servizio = arg.get('tipo_servizio')
        # Comunicazione
        comunicazione_id = arg.get('comunicazione_id', False)
        com_line_search = [('comunicazione_id','=',comunicazione_id), ('partner_id', '=', partner.id)]
        com_line_ids = self.search(cr, uid, com_line_search)
        # Valori documento
        val = {}
        doc_vals = self.pool.get('spesometro.comunicazione').compute_amounts(cr, uid, move, invoice, arg)
        # New partner
        if not com_line_ids:
            # p.iva
            if partner.vat:
                partita_iva = partner.vat[2:]
            else:
                partita_iva = '{:11s}'.format("".zfill(11))
            # prov. nascita
            prov_code = False
            '''
            >>>> mancano dati persona fisica
            if move.partner_id.birth_city.name:
                city_data = move.partner_id.address[0]._set_vals_city_data(cr, uid, {'city' : partner.birth_city.name})
                prov_id = city_data.get('province_id', False)
                if prov_id:
                    prov = self.pool.get('res.province').borwse(cr, uid, prov_id)
                    prov_nascita_code = prov.code
            '''
            val = {
                'comunicazione_id' : comunicazione_id,
                'partner_id' : partner.id,
                'codice_fiscale' : partner.fiscalcode or False,
                'codice_identificativo_IVA' : partner.vat or False,
                'noleggio' : partner.spesometro_leasing or False,
                'operazione_tipo_importo' : operazione_tipo_importo or False,
                
                ##'pf_cognome' : move.partner_id.fiscalcode_surname or False,
                ##'pf_nome' : move.partner_id.fiscalcode_firstname or False,
                ##'pf_data_nascita' : move.partner_id.birth_date or False,
                ##'pf_comune_stato_nascita' : move.partner_id.birth_city.name or False,
                ##'pf_provincia_nascita' : prov_code or False,
                ##'pf_codice_stato_estero' : move.partner_id.address[0].country_id.codice_stato_agenzia_entrate or '',
                'pg_denominazione' : partner.name or False,
                'pg_citta_estera_sede_legale' : partner.city or False,
                'pg_codice_stato_estero' : partner.country_id.codice_stato_agenzia_entrate or '',
                'pg_indirizzo_sede_legale' : partner.street or False,
                
                'operazione_fiscalita_privilegiata' : False,
                'operazione_con_soggetti_non_residenti' : False,
                'acquisto_servizi_da_soggetti_non_residenti' : False,
                }
            
            if operazione == 'BL1':
                val['operazione_fiscalita_privilegiata'] = True
            elif operazione == 'BL2':
                val['operazione_con_soggetti_non_residenti'] = True
            elif operazione == 'BL3':
                val['acquisto_servizi_da_soggetti_non_residenti'] = True    
            
            # attive
            if arg.get('segno', False) == 'attiva':
                
                # BL003 - Operazioni imponibili, non imponibili ed esenti
                if operazione_tipo_importo == 'INE':
                    val['attive_importo_complessivo'] = doc_vals.get('amount_total', 0)
                    val['attive_imposta'] = doc_vals.get('amount_tax', 0)
                # BL004 - Operazioni non soggette ad IVA
                elif operazione_tipo_importo == 'NS': 
                    if tipo_servizio == 'cessioni':
                        val['attive_non_sogg_cessione_beni'] = doc_vals.get('amount_total', 0)
                    else:
                        val['attive_non_sogg_servizi'] = doc_vals.get('amount_total', 0)
                # BL005 - Note di variazione
                elif operazione_tipo_importo == 'NV':
                    val['attive_note_variazione'] = doc_vals.get('amount_untaxed', 0)
                    val['attive_note_variazione_imposta'] = doc_vals.get('amount_tax', 0)
            # passive         
            else:
                # BL006 - Operazioni imponibili, non imponibili ed esenti
                if operazione_tipo_importo == 'INE':
                    val['passive_importo_complessivo'] = doc_vals.get('amount_total', 0)
                    val['passive_imposta'] = doc_vals.get('amount_tax', 0)
                # BL007 - Operazioni non soggette ad IVA
                elif operazione_tipo_importo == 'NS': 
                    val['passive_non_sogg_importo_complessivo'] = doc_vals.get('amount_total', 0)
                # BL008 - Note di variazione
                elif operazione_tipo_importo == 'NV':
                    val['passive_note_variazione'] = doc_vals.get('amount_untaxed', 0)
                    val['passive_note_variazione_imposta'] = doc_vals.get('amount_tax', 0)
                
        # Partner already exists
        if com_line_ids:
            for com_line in self.browse(cr, uid, com_line_ids):
                
                # attive
                if arg.get('segno', False) == 'attiva':
                    
                    # BL003 - Operazioni imponibili, non imponibili ed esenti
                    if operazione_tipo_importo == 'INE':
                        val['attive_importo_complessivo'] = \
                            com_line.attive_importo_complessivo + doc_vals.get('amount_total', 0)
                        val['attive_imposta'] = \
                            com_line.attive_imposta + doc_vals.get('amount_tax', 0)
                    # BL004 - Operazioni non soggette ad IVA
                    elif operazione_tipo_importo == 'NS': 
                        if tipo_servizio == 'cessioni':
                            val['attive_non_sogg_cessione_beni'] =\
                                com_line.attive_non_sogg_cessione_beni + doc_vals.get('amount_total', 0)
                        else:
                            val['attive_non_sogg_servizi'] = \
                                com_line.attive_non_sogg_servizi + doc_vals.get('amount_total', 0)
                    # BL005 - Note di variazione
                    elif operazione_tipo_importo == 'NV':
                        val['attive_note_variazione'] = \
                            com_line.attive_note_variazione + doc_vals.get('amount_untaxed', 0)
                        val['attive_note_variazione_imposta'] = \
                            com_line.attive_note_variazione_imposta + doc_vals.get('amount_tax', 0)
                # passive         
                else:
                    # BL006 - Operazioni imponibili, non imponibili ed esenti
                    if operazione_tipo_importo == 'INE':
                        val['passive_importo_complessivo'] = \
                            com_line.passive_importo_complessivo + doc_vals.get('amount_total', 0)
                        val['passive_imposta'] = \
                            com_line.passive_imposta + doc_vals.get('amount_tax', 0)
                    # BL007 - Operazioni non soggette ad IVA
                    elif operazione_tipo_importo == 'NS': 
                        val['passive_non_sogg_importo_complessivo'] = \
                            com_line.passive_non_sogg_importo_complessivo + doc_vals.get('amount_total', 0)
                    # BL008 - Note di variazione
                    elif operazione_tipo_importo == 'NV':
                        val['passive_note_variazione'] = \
                            com_line.passive_note_variazione + doc_vals.get('amount_untaxed', 0)
                        val['passive_note_variazione_imposta'] = \
                            com_line.passive_note_variazione_imposta + doc_vals.get('amount_tax', 0)
                
        if com_line_ids:
            line_id = com_line.id
            self.write(cr, uid, [com_line.id], val)
        else:
            line_id = self.create(cr, uid, val)
        
        return line_id
    
class spesometro_comunicazione_line_FE(orm.Model):

    _name = "spesometro.comunicazione.line.fe"
    _description = "Spesometro - Comunicazione linee quadro FE"
    _columns = {
        'comunicazione_id': fields.many2one('spesometro.comunicazione', 'Comunicazione', ondelete='cascade'),
        
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'partita_iva': fields.char('Partita IVA', size=11),
        'codice_fiscale': fields.char('Codice Fiscale', size=16),
        'documento_riepilogativo': fields.boolean('Documento Riepilogativo'),
        'noleggio': fields.selection((('A','Autovettura'), ('B','Caravan'), ('C','Altri Veicoli'), ('D','Unità  da diporto'), ('E','Aeromobii')),'Leasing'),
        
        'autofattura': fields.boolean('Autofattura'),
        'data_documento': fields.date('Data documento'),
        'data_registrazione': fields.date('Data registrazione'),
        'numero_fattura': fields.char('Numero Fattura - Doc riepilog.', size=16),
        
        'importo': fields.float('Importo', digits_compute=dp.get_precision('Account')),
        'imposta': fields.float('Imposta', digits_compute=dp.get_precision('Account')),
        }
    
class spesometro_comunicazione_line_FR(orm.Model):

    _name = "spesometro.comunicazione.line.fr"
    _description = "Spesometro - Comunicazione linee quadro FR"
    _columns = {
        'comunicazione_id': fields.many2one('spesometro.comunicazione', 'Comunicazione', ondelete='cascade'),
        
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'partita_iva': fields.char('Partita IVA', size=11),
        'documento_riepilogativo': fields.boolean('Documento Riepilogativo'),
        'data_documento': fields.date('Data documento'),
        'data_registrazione': fields.date('Data registrazione'),
        'iva_non_esposta': fields.boolean('IVA non esposta'),
        'reverse_charge': fields.boolean('Reverse charge'),
        'autofattura': fields.boolean('Autofattura'),
        
        'importo': fields.float('Importo', digits_compute=dp.get_precision('Account')),
        'imposta': fields.float('Imposta', digits_compute=dp.get_precision('Account')),
        }

class spesometro_comunicazione_line_NE(orm.Model):

    _name = "spesometro.comunicazione.line.ne"
    _description = "Spesometro - Comunicazione linee quadro NE"
    _columns = {
        'comunicazione_id': fields.many2one('spesometro.comunicazione', 'Comunicazione', ondelete='cascade'),
        
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'partita_iva': fields.char('Partita IVA', size=11),
        'codice_fiscale': fields.char('Codice Fiscale', size=16),
        'data_emissione': fields.date('Data emissione'),
        'data_registrazione': fields.date('Data registrazione'),
        'numero_nota': fields.char('Numero Nota', size=16),
        
        'importo': fields.float('Importo', digits_compute=dp.get_precision('Account')),
        'imposta': fields.float('Imposta', digits_compute=dp.get_precision('Account')),
        }

class spesometro_comunicazione_line_NR(orm.Model):

    _name = "spesometro.comunicazione.line.nr"
    _description = "Spesometro - Comunicazione linee quadro NR"
    _columns = {
        'comunicazione_id': fields.many2one('spesometro.comunicazione', 'Comunicazione', ondelete='cascade'),
        
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'partita_iva': fields.char('Partita IVA', size=11),
        'data_documento': fields.date('Data documento'),
        'data_registrazione': fields.date('Data registrazione'),
        
        'importo': fields.float('Importo', digits_compute=dp.get_precision('Account')),
        'imposta': fields.float('Imposta', digits_compute=dp.get_precision('Account')),
        }
    
class spesometro_comunicazione_line_DF(orm.Model):

    _name = "spesometro.comunicazione.line.df"
    _description = "Spesometro - Comunicazione linee quadro DF"
    _columns = {
        'comunicazione_id': fields.many2one('spesometro.comunicazione', 'Comunicazione', ondelete='cascade'),
        
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'codice_fiscale': fields.char('Codice Fiscale', size=16),
        'data_operazione': fields.date('Data operazione'),
        
        'importo': fields.float('Importo', digits_compute=dp.get_precision('Account')),
        'noleggio': fields.selection((('A','Autovettura'), ('B','Caravan'), ('C','Altri Veicoli'), ('D','Unità  da diporto'), ('E','Aeromobii')),'Leasing'),
        }     
    
class spesometro_comunicazione_line_FN(orm.Model):

    _name = "spesometro.comunicazione.line.fn"
    _description = "Spesometro - Comunicazione linee quadro FN"
    _columns = {
        'comunicazione_id': fields.many2one('spesometro.comunicazione', 'Comunicazione', ondelete='cascade'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        
        'pf_cognome': fields.char('Cognome', size=24, help=""),
        'pf_nome': fields.char('Nome', size=20, help=""),
        'pf_data_nascita': fields.date('Data di nascita'),
        'pf_comune_stato_nascita': fields.char('Comune o stato estero di nascita', size=40),
        'pf_provincia_nascita': fields.char('Provincia', size=2),
        'pf_codice_stato_estero_domicilio': fields.char('Codice Stato Estero del Domicilio', size=3, help="Deve essere uno di quelli presenti nella tabella 'elenco dei paesi e\
                    territori esteri' pubblicata nelle istruzioni del modello Unico"),
        
        'pg_denominazione': fields.char('Denominazione/Ragione sociale', size=60),
        'pg_citta_estera_sede_legale': fields.char('Città estera delle Sede legale', size=40),
        'pg_codice_stato_estero_domicilio': fields.char('Codice Stato Estero del Domicilio', size=3, help="Deve essere uno di quelli presenti nella tabella 'elenco dei paesi e\
                    territori esteri' pubblicata nelle istruzioni del modello Unico"),
        'pg_indirizzo_sede_legale': fields.char('Indirizzo legale', size=40),
        
        'data_emissione': fields.date('Data emissione'),
        'data_registrazione': fields.date('Data registrazione'),
        'numero_fattura': fields.char('Numero Fattura/Doc riepilog.', size=16),
        'noleggio': fields.selection((('A','Autovettura'), ('B','Caravan'), ('C','Altri Veicoli'), ('D','Unità  da diporto'), ('E','Aeromobii')),'Leasing'),
        
        'importo': fields.float('Importo', digits_compute=dp.get_precision('Account')),
        'imposta': fields.float('Imposta', digits_compute=dp.get_precision('Account')),
        }  
    
    
class spesometro_comunicazione_line_SE(orm.Model):
    '''
    QUADRO SE - Acquisti di servizi da non residenti e Acquisti da operatori di San Marino
    '''
    _name = "spesometro.comunicazione.line.se"
    _description = "Spesometro - Comunicazione linee quadro SE"
    _columns = {
        'comunicazione_id': fields.many2one('spesometro.comunicazione', 'Comunicazione', ondelete='cascade'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        
        'pf_cognome': fields.char('Cognome', size=24, help=""),
        'pf_nome': fields.char('Nome', size=20, help=""),
        'pf_data_nascita': fields.date('Data di nascita'),
        'pf_comune_stato_nascita': fields.char('Comune o stato estero di nascita', size=40),
        'pf_provincia_nascita': fields.char('Provincia', size=2),
        'pf_codice_stato_estero_domicilio': fields.char('Codice Stato Estero del Domicilio', size=3, help="Deve essere uno di quelli presenti nella tabella 'elenco dei paesi e\
                    territori esteri' pubblicata nelle istruzioni del modello Unico"),
        
        'pg_denominazione': fields.char('Denominazione/Ragione sociale', size=60),
        'pg_citta_estera_sede_legale': fields.char('Città estera delle Sede legale', size=40),
        'pg_codice_stato_estero_domicilio': fields.char('Codice Stato Estero del Domicilio', size=3, help="Deve essere uno di quelli presenti nella tabella 'elenco dei paesi e\
                    territori esteri' pubblicata nelle istruzioni del modello Unico"),
        'pg_indirizzo_sede_legale': fields.char('Indirizzo legale', size=40),
        
        'codice_identificativo_IVA': fields.char('Codice Identificativo IVA (037=San Marino)', size=3),
        'data_emissione': fields.date('Data emissione'),
        'data_registrazione': fields.date('Data registrazione'),
        'numero_fattura': fields.char('Numero Fattura/Doc riepilog.', size=16),
        
        'importo': fields.float('Importo/imponibile', digits_compute=dp.get_precision('Account')),
        'imposta': fields.float('Imposta', digits_compute=dp.get_precision('Account')),
        }
    
    def add_line(self, cr, uid, move, invoice, arg):
        comunicazione_lines_obj = self.pool.get('spesometro.comunicazione.line.se')
        # Partner
        if 'partner' in arg and arg['partner']:
            partner = arg['partner']
        else:
            partner = move.partner_id
        # Comunicazione
        comunicazione_id = arg.get('comunicazione_id', False)
        com_line_search = [('comunicazione_id','=',comunicazione_id), ('partner_id', '=', partner.id)]
        com_line_ids = self.search(cr, uid, com_line_search)
        # Valori documento
        val = {}
        doc_vals = self.pool.get('spesometro.comunicazione').compute_amounts(cr, uid, move, invoice, arg)
        # p.iva
        if partner.vat:
            partita_iva = partner.vat[2:]
        else:
            partita_iva = '{:11s}'.format("".zfill(11))
        # prov. nascita
        '''
        >> dati persona fisica>> da aggiungere
        prov_code = False
        if move.partner_id.birth_city.name:
            city_data = move.partner_id.address[0]._set_vals_city_data(cr, uid, {'city' : move.partner_id.birth_city.name})
            prov_id = city_data.get('province_id', False)
            if prov_id:
                prov = self.pool.get('res.province').borwse(cr, uid, prov_id)
                prov_nascita_code = prov.code
        '''
        # Indirizzo
        address = self.pool.get('spesometro.comunicazione')._get_partner_address_obj(cr, uid, move, invoice, arg)
        # Codice identificativo IVA -Da indicare esclusivamente per operazioni con San Marino (Codice Stato = 037)
        codice_identificativo_iva=''
        if self.pool.get('spesometro.comunicazione').partner_is_from_san_marino(cr, uid, move, invoice, arg):
            codice_identificativo_iva = '037'
        val = {
            'comunicazione_id' : comunicazione_id,
            'partner_id' : partner.id,
            'codice_fiscale' : partner.fiscalcode or False,
            'noleggio' : partner.spesometro_leasing or False,
            
            #'pf_cognome' : move.partner_id.fiscalcode_surname or False,
            #'pf_nome' : move.partner_id.fiscalcode_firstname or False,
            #'pf_data_nascita' : move.partner_id.birth_date or False,
            #'pf_comune_stato_nascita' : move.partner_id.birth_city.name or False,
            #'pf_provincia_nascita' : prov_code or False,
            #'pf_codice_stato_estero_domicilio' : address.country_id.codice_stato_agenzia_entrate or codice_identificativo_iva or '',
            
            'pg_denominazione' : partner.name or False,
            'pg_citta_estera_sede_legale' : address.city or False,
            'pg_codice_stato_estero_domicilio' : address.country_id.codice_stato_agenzia_entrate or codice_identificativo_iva or '',
            'pg_indirizzo_sede_legale' : address.street or False,
            
            'codice_identificativo_IVA' : codice_identificativo_iva,
            
            'data_emissione': move.date,
            'data_registrazione': invoice.date_invoice or move.date,
            'numero_fattura': move.name,
            
            'importo': doc_vals.get('amount_untaxed', 0),
            'imposta': doc_vals.get('amount_tax', 0)
            }
        
        line_id = self.create(cr, uid, val)
        
        return line_id  
    
class spesometro_comunicazione_line_TU(orm.Model):

    _name = "spesometro.comunicazione.line.tu"
    _description = "Spesometro - Comunicazione linee quadro TU"
    _columns = {
        'comunicazione_id': fields.many2one('spesometro.comunicazione', 'Comunicazione', ondelete='cascade'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        
        'cognome': fields.char('Cognome', size=24, help=""),
        'nome': fields.char('Nome', size=20, help=""),
        'data_nascita': fields.date('Data di nascita'),
        'comune_stato_nascita': fields.char('Comune o stato estero di nascita', size=40),
        'provincia_nascita': fields.char('Provincia', size=2),
        'citta_estera_residenza': fields.char('Città Estera di residenza', size=40),
        'codice_stato_estero': fields.char('Codice Stato Estero', size=3, help="Deve essere uno di quelli presenti nella tabella 'elenco dei paesi e\
                    territori esteri' pubblicata nelle istruzioni del modello Unico"),
        'indirizzo_estero_residenza': fields.char('Indirizzo Estero di residenza', size=40),
        
        'data_emissione': fields.date('Data emissione'),
        'data_registrazione': fields.date('Data registrazione'),
        'numero_fattura': fields.char('Numero Fattura/Doc riepilog.', size=16),
        
        'importo': fields.float('Importo/imponibile', digits_compute=dp.get_precision('Account')),
        'imposta': fields.float('Imposta', digits_compute=dp.get_precision('Account')),
        }  
