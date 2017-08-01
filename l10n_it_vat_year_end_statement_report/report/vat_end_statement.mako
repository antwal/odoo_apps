<html>
<head>
    <style type="text/css">
        ${css}
    </style>
</head>
<body>
    <h2>Liquidazione IVA Annuale - ${ year() }</h2>
    <% total = {'credit': 0.0, 'debit': 0.0} %>
    %for type in ('debit', 'credit'):
        <h3 class="type">${ type=='credit' and 'Acquisti' or 'Vendite' }</h3>
        <table class="table table-bordered table-condensed">
            <thead>
                <tr>
                    <th style="width:50%;">Descrizione</th>
                    <th style="width:25%;">Imponibile</th>
                    <th style="width:25%;">Imposta</th>
                </tr>
            </thead>
            <tbody>
                <% total_base = total_vat = 0.0 %>
                <% taxes = tax_codes_amounts(type) %>
                %for tax,vals in taxes.items():
                <tr>
                    <td>${ tax }</td>
                    <td class="amount">${ formatLang(vals['base'])|entity }</td>
                    <td class="amount">${ formatLang(vals['vat'])|entity }</td>
                </tr>
                <% total_base += vals['base'] %>
                <% total_vat += vals['vat'] %>
                <% total[type] += vals['vat'] %>
                %endfor
                <tr>
                    <td></td>
                    <td class="total amount">${ formatLang(total_base)|entity }</td>
                    <td class="total amount">${ formatLang(total_vat)|entity }</td>
                </tr>
            </tbody>
        </table>
    %endfor
    ##
    ## Totale IVA periodo
    ##
    <h3 class="type">${ 'Totali'}</h3>
    <% total_end_vat_period = total['debit'] + total['credit'] %>
    ##<table class="table table-bordered table-condensed" style="margin-left:20%;width:80%;">
    <table class="table table-bordered table-condensed" >
        <tr>
            <td style="width:80%;" class="amount" colspan="3">Iva Debito</td>
            <td style="width:20%;" class="amount">${ formatLang(total['debit'])|entity }</td>
        </tr>
        <tr>
            <td colspan="3" class="amount">Iva Credito</td>
            <td class="amount">${ formatLang(total['credit'])|entity }</td>
        </tr>
        ## Altra iva x compensazioni
        <% generic_lines = lines_generic_amounts() %>
        <% total_generic = 0.0 %>
        
        %if generic_lines:
        	<tr>
        		<td colspan="3">Altra IVA per compensazioni o interessi</td>
            	<td class="amount"></td>
        	</tr>	
        %endif
        %for gen_data in generic_lines:
        	<tr>
        		<td>${gen_data['period'] |entity } </td>
        		<td style="width:200px;">${gen_data['description'] |entity } - ${gen_data['account_name'] |entity }</td>
            	<td class="amount">${ formatLang(gen_data['amount']) |entity } </td>
            	<td></td>
        	</tr>
        	<% total_generic += gen_data['amount'] %>
        %endfor
        
        ##<tr>
        ## 	<td>test</td>
        ##    <td class="amount">test</td>
        ##    <td class="amount">${total_generic |entity } </td>
        ##</tr>
        
        %if total_generic:
        	<tr>
        		<td class="amount"> </td>
        		<td colspan="2" class="amount"> Totale Altra IVA per compensazioni o interessi</td>
            	<td  class="amount">${ formatLang(total_generic) |entity } </td>
        	</tr>	
        %endif
        
        
        <% total_end_vat_period = total_end_vat_period + total_generic %>
        ##
        ## Iva a credito/debito del periodo
        ##
        <tr>
        %if total_end_vat_period > 0:
            <td class="total" colspan="3">IVA del Periodo Da Versare</td>
        %else:
        	<td class="total" colspan="3">IVA del Periodo A Credito</td>
        %endif
            <td class="total amount">${ formatLang(total_end_vat_period)|entity }</td>
        </tr>
        
    </table>
    ##
    ## Versamenti e altri crediti e debiti
    ##
    % if amount_paid() > 0:
    <% total_to_pay = total_end_vat_period -  amount_paid() %>
    <table class="table table-bordered table-condensed" style="margin-left:50%;width:50%;">
        <tr>
            <td style="width:50%;">Iva Versata</td>
            <td style="width:50%;" class="amount">${ formatLang(amount_paid()) |entity } </td>
        </tr>
        <tr>
        	 %if total_to_pay > 0:
            	<td class="total">Totale IVA Da Versare</td>
        	%else:
        		<td class="total">Totale IVA A Credito</td>
        	%endif
            <td style="width:50%;" class="total amount">${ formatLang(total_to_pay)|entity } </td>
        </tr>
    </table>
    %endif
</body>
</html>
