"""Valuation SAPR4 (Sanepar) - DCF de FCFF + checagem por múltiplos.

Data-base do balanço: 30/06/2026 (ITR 2T26). Data da avaliação: 30/09/2026.
Cotação: SAPR4 R$ 6,56 / SAPR3 R$ 7,19 (pregão 28/09/2026, valuation_SAPR4.md §1).
Valores em R$ milhões correntes. Premissas aprovadas pelo usuário em 30/09/2026.

Fontes dos números da companhia (Drive, pasta robo-cvm-claude/empresas/SAPR4_76484013000145):
  [VAL]  valuation_SAPR4.md
  [R2T]  2026-2T release 2T26 (texto integral em 2026-2T/dossie.md)
  [R4T]  2025-4T release 4T25 (2025-4T/dossie.md)
  [ITR]  2026-2T ITR, notas explicativas (2026-2T/texto/..._notas.txt)
  [PPI]  fato relevante 11/12/2025 - Plano Plurianual de Investimentos 2026-2030
"""

# ---------------------------------------------------------------- dados da companhia
ACOES_ON = 503.735259          # milhões [VAL §1]
ACOES_PN = 1007.470260         # milhões [VAL §1]
PRECO_PN, PRECO_ON = 6.56, 7.19  # 28/09/2026 [VAL §1]

REC_6M26 = 3847.5              # receita líquida 6M26 [R2T p.7]
REC_2S25 = 1804.2 + 1891.0     # 3T25 + 4T25 [VAL §4]
CAPEX_6M26 = 579.2 + 555.3     # DFC 1T26 + 2T26 [VAL §4]
EBITDA_AJ_TTM = 3101.5 - 1515.3 + 1643.4   # 2025 aj. [R4T] - 6M25 aj. + 6M26 aj. [R2T p.11]
LL_AJ_TTM = 1584.5 - 756.0 + 950.0          # idem, lucro ajustado
RECEITA_FIN_FLOAT = (381.1 - 131.8) * 2 * (1 - 0.34)  # receita de aplicações 6M26 - 6M25 [R2T p.10], anualizada e líquida de IR
LL_NORM = LL_AJ_TTM - RECEITA_FIN_FLOAT

# base de ativos para D&A: intangível + imobilizado + ativos de contrato em 30/06/2026 [R2T p.25]
BASE_ATIVOS_0 = 12943.9 + 432.4 + 4143.0
TAXA_DA = 0.040                # D&A anualizada 2026 ~ 347,3*2 [R2T p.13] / base ~ 4%

# dívida em 30/06/2026 [R2T p.15; ITR nota 13]
DIVIDA_BRUTA = 7250.0
ARRENDAMENTOS = 304.4 + 220.1  # litoral + direito de uso (pagamentos saem do FCFF)
CAIXA = 4662.5                 # [R2T p.25]
PASSIVO_REG = 4407.957         # [ITR nota 20]
PREV_SAUDE = 78.2 + 1094.4     # [R2T p.26]
PROVISOES = 578.3              # prováveis [ITR nota 17]
DEP_JUDICIAIS = 399.4          # [R2T p.25]
CONTING_POSSIVEIS = 1915.5     # [ITR nota 17]
T_STAT = 0.34

# plano de investimentos, total sem doações de redes [PPI]
PLANO = {2026: 2623.9 - 39.9, 2027: 2420.6 - 43.2, 2028: 2165.8 - 42.8,
         2029: 2973.3 - 43.2, 2030: 2893.4 - 43.7}
LEASE_ANUAL_2026 = 4 * (39.9 + 7.4)   # arrendamentos + PPP pagos no 2T26, anualizado [R2T p.27]

# macro (Focus 28/09/2026; Selic/CDI para o rendimento do caixa)
IPCA = {2026: .0499, 2027: .0431, 2028: .0380}
IPCA_LP = .035
CDI = {2026: .1370, 2027: .1250, 2028: .1100}
CDI_LP = .1050
ipca = lambda y: IPCA.get(y, IPCA_LP)
cdi = lambda y: CDI.get(y, CDI_LP)

ANOS = list(range(2026, 2036))   # 2026 = só 2S26

CENARIOS = {
    "pessimista": dict(rf=.074, beta=.95, erp=.055, kd=.080, t_ebit=.34, g2s=.040, g1=.020,
                       margem=.39, capex_fator=1.10, ronic=.070, g_term=.005,
                       share_reg=1.00, conting=.20),
    "base":       dict(rf=.072, beta=.80, erp=.050, kd=.077, t_ebit=.30, g2s=.056, g1=.030,
                       margem=.42, capex_fator=1.00, ronic=.0808, g_term=.010,
                       share_reg=1.00, conting=0.0),
    "otimista":   dict(rf=.070, beta=.70, erp=.045, kd=.074, t_ebit=.29, g2s=.070, g1=.040,
                       margem=.44, capex_fator=.90, ronic=.090, g_term=.015,
                       share_reg=.75, conting=0.0),
}
PESOS = {"pessimista": .25, "base": .50, "otimista": .25}
DV = 0.35   # D/(D+E) meta


def taxas(p):
    ke = p["rf"] + p["beta"] * p["erp"]
    wacc = (1 - DV) * ke + DV * p["kd"] * (1 - T_STAT)
    return ke, wacc


def custo_passivo_regulatorio(share):
    """Caixa necessário hoje, aplicado a CDI líquido de IR, para liquidar o passivo.
    O saldo corrige a 8,08% real + IPCA (não dedutível) [ITR nota 20].
    Metade em descontos (set/2026 a mai/2029), metade em capex (jul/2026 a dez/2030)."""
    saldo_tar = saldo_cap = PASSIVO_REG * share / 2
    n_tar = 33   # meses set/26..mai/29
    n_cap = 54   # meses jul/26..dez/30
    pv, fator = 0.0, 1.0
    for m in range(54):
        ano = 2026 + (6 + m) // 12
        acr = ((1.0808) * (1 + ipca(ano))) ** (1 / 12) - 1
        saldo_tar *= 1 + acr
        saldo_cap *= 1 + acr
        pg = 0.0
        if 2 <= m < 2 + n_tar:
            pg_t = saldo_tar / (2 + n_tar - m); saldo_tar -= pg_t; pg += pg_t
        pg_c = saldo_cap / (n_cap - m); saldo_cap -= pg_c; pg += pg_c
        fator /= (1 + cdi(ano) * (1 - T_STAT)) ** (1 / 12)
        pv += pg * fator
    return pv


def dcf(p, margem=None, wacc_real=None, g_term=None, rtp2029=0.0, ronic=None, coerente=True):
    """coerente=True: o lucro operacional cresce pela inflação + retorno `ronic` (real) sobre o
    investimento líquido do ano anterior (lógica regulatória: capex entra na base e é remunerado).
    coerente=False: leitura literal das premissas (receita cresce g1 real, independente do capex)."""
    margem = p["margem"] if margem is None else margem
    g_term = p["g_term"] if g_term is None else g_term
    ke, wacc = taxas(p)
    wacc = wacc if wacc_real is None else wacc_real
    t = p["t_ebit"]
    ronic = p["ronic"] if ronic is None else ronic
    nopat_prev = inv_prev = None

    linhas, base_at, pv, fd = [], BASE_ATIVOS_0, 0.0, 1.0
    rec_ant_anual = REC_6M26 + REC_2S25        # receita 2025 "calendário" p/ capital de giro
    rec_anual = REC_6M26 + REC_2S25 * (1 + p["g2s"])
    lease = LEASE_ANUAL_2026
    rr_2030 = None
    for i, ano in enumerate(ANOS):
        frac = 0.5 if ano == 2026 else 1.0
        if ano > 2026:
            if ano <= 2030:
                g_real = p["g1"]
            else:  # converge linearmente de g1 (2030) ao g da perpetuidade (2036)
                g_real = p["g1"] + (g_term - p["g1"]) * (ano - 2030) / 6
            rec_ant_anual = rec_anual
            rec_anual = rec_anual * (1 + ipca(ano)) * (1 + g_real) * ((1 + rtp2029) if ano == 2029 else 1)
            lease *= 1 + ipca(ano)
        da = TAXA_DA * base_at * frac
        if coerente and ano > 2026:
            nopat = nopat_prev * (1 + ipca(ano)) + ronic * (1 + ipca(ano)) * inv_prev
            ebit = nopat / (1 - t)
            ebitda = ebit + lease + da
            rec_anual = ebitda / margem
            rec = rec_anual
        else:
            rec = REC_2S25 * (1 + p["g2s"]) if ano == 2026 else rec_anual
            ebitda = margem * rec
            ebit = ebitda - lease * frac - da
        imposto = t * max(ebit, 0)
        nopat = ebit - imposto
        if ano <= 2030:
            capex = (PLANO[ano] - CAPEX_6M26 if ano == 2026 else PLANO[ano]) * p["capex_fator"]
            if ano == 2030:
                rr_2030 = (capex - da) / nopat
        else:
            # base regulatória indexada ao IPCA: só o crescimento REAL exige reinvestimento
            rr_term = g_term / ronic
            rr = rr_2030 + (rr_term - rr_2030) * (ano - 2030) / 5
            capex = da + rr * nopat
        dncg = 0.10 * (rec_anual - rec_ant_anual) * frac
        if ano == 2026:   # anualiza 2026 como ponto de partida
            nopat_prev = 2 * nopat
            inv_prev = PLANO[2026] * p["capex_fator"] - 2 * da
        else:
            nopat_prev, inv_prev = nopat, capex - da
        fcff = ebitda - lease * frac - imposto - capex - dncg
        base_at += capex - da
        # desconto no meio do período, WACC nominal ano a ano
        w_nom = (1 + wacc) * (1 + ipca(ano)) - 1
        if ano == 2026:
            fd_mid = (1 + w_nom) ** -0.25; fd = (1 + w_nom) ** -0.5
        else:
            fd_mid = fd * (1 + w_nom) ** -0.5; fd = fd * (1 + w_nom) ** -1
        pv += fcff * fd_mid
        linhas.append((ano, rec, ebitda, da, ebit, imposto, capex, dncg, fcff, nopat / max(base_at, 1)))

    # perpetuidade (Gordon) a partir de 2036
    g_nom = (1 + IPCA_LP) * (1 + g_term) - 1
    w_nom_lp = (1 + wacc) * (1 + IPCA_LP) - 1
    nopat_2036 = linhas[-1][4] * (1 - t) * (1 + g_nom)
    fcff_2036 = nopat_2036 * (1 - g_term / ronic)   # reinvestimento = g real / RONIC real
    tv = fcff_2036 / (w_nom_lp - g_nom)
    pv_tv = tv * fd
    ev = pv + pv_tv

    reg = custo_passivo_regulatorio(p["share_reg"])
    divida_liq_ajustada = (DIVIDA_BRUTA - ARRENDAMENTOS - CAIXA + reg
                           + PREV_SAUDE * (1 - T_STAT)
                           + (PROVISOES - DEP_JUDICIAIS) * (1 - T_STAT)
                           + p["conting"] * CONTING_POSSIVEIS)
    eq_jun = ev - divida_liq_ajustada
    eq_set = eq_jun * (1 + (1 + ke) * (1 + ipca(2026)) - 1) ** 0.25
    on = eq_set / (ACOES_ON + 1.1 * ACOES_PN)
    res = dict(ke=ke, wacc=wacc, ev=ev, pv_exp=pv, pv_tv=pv_tv, tv_share=pv_tv / ev,
               reg=reg, dl_aj=divida_liq_ajustada, equity=eq_set,
               pn=1.1 * on, on=on, igual=eq_set / (ACOES_ON + ACOES_PN), linhas=linhas)
    return res


def fmt(x, d=0):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


if __name__ == "__main__":
    import sys
    mc = ACOES_ON * PRECO_ON + ACOES_PN * PRECO_PN
    print(f"Valor de mercado 28/09/2026: {fmt(mc,1)} | LL ajustado TTM {fmt(LL_AJ_TTM,1)} | LL normalizado {fmt(LL_NORM,1)}")
    todos = {}
    for modo, coer in [("LITERAL (receita independe do capex)", False), ("COERENTE (capex remunerado ao RONIC)", True)]:
        print(f"\n################ {modo} ################")
        res = {}
        for nome, p in CENARIOS.items():
            r = dcf(p, coerente=coer); res[nome] = r
            print(f"\n=== {nome.upper()} ===  Ke real {r['ke']:.2%}  WACC real {r['wacc']:.2%}")
            print(f"{'ano':>5}{'receita':>10}{'EBITDA':>9}{'D&A':>7}{'EBIT':>8}{'IR':>7}{'capex':>8}{'dNCG':>6}{'FCFF':>8}{'ROIC':>7}")
            for l in r["linhas"]:
                print(f"{l[0]:>5}{fmt(l[1]):>10}{fmt(l[2]):>9}{fmt(l[3]):>7}{fmt(l[4]):>8}{fmt(l[5]):>7}{fmt(l[6]):>8}{fmt(l[7]):>6}{fmt(l[8]):>8}{l[9]:>7.1%}")
            ls = r["linhas"]
            g_real_implicito = ((ls[4][1] / ls[1][1]) / ((1+ipca(2028))*(1+ipca(2029))*(1+ipca(2030)))) ** (1/3) - 1
            print(f"Crescimento real implícito da receita 2027-30: {g_real_implicito:.1%} a.a.")
            print(f"VP explícito {fmt(r['pv_exp'])} | VP perpetuidade {fmt(r['pv_tv'])} ({r['tv_share']:.0%} do EV) | EV {fmt(r['ev'])}")
            print(f"Passivo regulatório econômico {fmt(r['reg'])} (contábil x share {fmt(PASSIVO_REG*p['share_reg'])})")
            print(f"Dívida líquida ajustada {fmt(r['dl_aj'])} | Equity 30/09 {fmt(r['equity'])}")
            print(f"SAPR4 {fmt(r['pn'],2)} | SAPR3 {fmt(r['on'],2)} | valor igual por ação {fmt(r['igual'],2)}")
        pond_pn = sum(PESOS[k] * res[k]["pn"] for k in res)
        pond_ig = sum(PESOS[k] * res[k]["igual"] for k in res)
        print(f"\nPonderado SAPR4 (PN=1,1xON): R$ {fmt(pond_pn,2)} | vs R$ 6,56: {pond_pn/PRECO_PN-1:+.1%} | margem de segurança {1-PRECO_PN/pond_pn:.1%}")
        print(f"Ponderado valor igual por ação: R$ {fmt(pond_ig,2)} | preço-teto com margem de 25%: R$ {fmt(0.75*pond_pn,2)}")
        todos[coer] = res

    b = CENARIOS["base"]
    print("\nSensibilidade SAPR4 (base coerente) - WACC real x g real perpetuidade")
    gs = [0.0, .005, .010, .015, .020]
    print("WACC\\g " + "".join(f"{g:>8.1%}" for g in gs))
    for w in [.075, .080, .085, .0906, .095, .100]:
        print(f"{w:>6.2%} " + "".join(f"{fmt(dcf(b, wacc_real=w, g_term=g)['pn'],2):>8}" for g in gs))

    print("\nSensibilidade SAPR4 (base coerente) - RONIC real x margem EBITDA")
    ms = [.38, .40, .42, .44, .46]
    print("RONIC  " + "".join(f"{m:>8.0%}" for m in ms))
    for ro in [.060, .070, .0808, .090, .100]:
        print(f"{ro:>6.2%} " + "".join(f"{fmt(dcf(b, ronic=ro, margem=m)['pn'],2):>8}" for m in ms))

    print("\nMúltiplos (pares privatizados; desconto de 35% por controle estatal)")
    fator_pn = 1.1 * (ACOES_ON + ACOES_PN) / (ACOES_ON + 1.1 * ACOES_PN)
    dl_aj_base = todos[True]["base"]["dl_aj"]
    for nome, mult in [("EV/EBITDA pares ~8,0x", 8.0), ("EV/EBITDA c/ desconto (5,2x)", 8.0 * .65)]:
        eq = mult * EBITDA_AJ_TTM - dl_aj_base
        print(f"{nome}: equity {fmt(eq)} -> SAPR4 {fmt(eq/(ACOES_ON+ACOES_PN)*fator_pn,2)}")
    for nome, mult in [("P/L pares ~14,3x", 14.3), ("P/L c/ desconto (9,3x)", 14.3 * .65)]:
        eq = mult * LL_NORM
        print(f"{nome} s/ LL normalizado: equity {fmt(eq)} -> SAPR4 {fmt(eq/(ACOES_ON+ACOES_PN)*fator_pn,2)}")
    ev_mkt = mc + dl_aj_base
    print(f"Mercado hoje: EV ajustado {fmt(ev_mkt)} = {ev_mkt/EBITDA_AJ_TTM:.1f}x EBITDA aj. TTM; P/L normalizado {mc/LL_NORM:.1f}x")

    por_pn = lambda total: total / (ACOES_ON + 1.1 * ACOES_PN) * 1.1
    for nome, po in [("pessimista", .25), ("base", .30), ("otimista", .40)]:
        d = por_pn(po * LL_NORM)
        print(f"DY {nome} (payout {po:.0%} do LL normalizado): R$ {fmt(d,3)}/PN = {d/PRECO_PN:.1%}")
