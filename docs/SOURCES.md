# Sources

Generated 2026-11-14 by `python tools/sources_report.py`. The live view is the Monitoring page of the site.

## Summary

| Status | Sources | Meaning |
|---|---:|---|
| no_portal_known | 713 | The Excel has no website or career URL for this company |
| pending_discovery | 585 | Career page or website on file, recruitment system not analysed yet (automatic, first runs) |
| ok | 21 | Read successfully on the last run |

## Sources successfully monitored

| Company | Offices | System | Board | Postings on board | Matching early-career roles | Evidence |
|---|---|---|---|---:|---:|---|
| AlixPartners | Dubai, London, Milan | greenhouse | `alixpartners` | 132 | 1 | Greenhouse board name 'AlixPartners', 132 postings, checked live 2026-11-13 |
| BlueCrest Capital | Dubai | smartrecruiters | `bluecrest` | 1 | 0 | SmartRecruiters company name 'BlueCrest', 1 posting, checked live 2026-11-13 |
| EQT | London, Luxembourg | greenhouse | `eqtpartners` | 11 | 0 | Greenhouse board name 'EQT Group', 11 postings, checked live 2026-11-13 |
| Engelhart (ECTP) | Dubai | greenhouse | `engelhart` | 3 | 0 | Greenhouse board name 'Engelhart', 3 postings, checked live 2026-11-13 |
| ExodusPoint Capital Management | Dubai | greenhouse | `exoduspoint` | 3 | 0 | Greenhouse board name 'ExodusPoint', 3 postings, checked live 2026-11-13 |
| GSA Capital | Dubai | greenhouse | `gsacapital` | 12 | 1 | Greenhouse board name 'GSA', 12 postings (11 in London), checked live 2026-11-13 |
| General Atlantic | Dubai | greenhouse | `generalatlantic` | 12 | 0 | Greenhouse board name 'General Atlantic', 12 postings, checked live 2026-11-13 |
| IQ-EQ Luxembourg S.A. | Luxembourg | smartrecruiters | `iqeq` | 117 | 0 | SmartRecruiters company name 'IQ-EQ', 117 postings, checked live 2026-11-13 |
| Lincoln International | London, Milan | greenhouse | `lincolninternational` | 36 | 3 | Greenhouse board name 'Lincoln International', 36 postings, checked live 2026-11-13 |
| Man Group | London | greenhouse | `mangroup` | 66 | 2 | Greenhouse board name 'Man Group', 66 postings, checked live 2026-11-13 |
| Oak Hill Advisors | Dubai | greenhouse | `oakhilladvisors` | 6 | 0 | Greenhouse board name 'Oak Hill Advisors', 6 postings, checked live 2026-11-13 |
| Partners Group | Zug | successfactors | `https://jobs.partnersgroup.com` | 76 | 3 | SuccessFactors career site linked from partnersgroup.com/en/careers; search page listed 76 postings, checked live 2026-11-13 |
| Point72 | Dubai, Sydney | greenhouse | `point72` | 200 | 4 | Greenhouse board name 'Point72', 200 postings, checked live 2026-11-13 |
| Qube Research and Technologies (QRT) | Dubai | greenhouse | `quberesearchandtechnologies` | 210 | 4 | Greenhouse board name 'Qube Research & Technologies', 210 postings, checked live 2026-11-13 |
| Schonfeld Strategic Advisors | Dubai | greenhouse | `schonfeld` | 70 | 2 | Greenhouse board name 'Schonfeld', 70 postings, checked live 2026-11-13 |
| Squarepoint Capital | Dubai | greenhouse | `squarepointcapital` | 90 | 6 | Greenhouse board name 'Squarepoint Capital', 90 postings, checked live 2026-11-13 |
| Swissquote Bank SA | Geneva | smartrecruiters | `swissquote` | 36 | 0 | SmartRecruiters company name 'Swissquote', 36 postings, checked live 2026-11-13 |
| Teneo (Financial Advisory) | London | greenhouse | `teneo` | 57 | 1 | Greenhouse board name 'Teneo', 57 postings, checked live 2026-11-13 |
| Tikehau Capital | Milan | smartrecruiters | `tikehaucapital` | 1 | 0 | SmartRecruiters company name 'Tikehau Capital', 1 posting, checked live 2026-11-13 |
| William Blair | London | greenhouse | `williamblair` | 48 | 6 | Greenhouse board name 'William Blair', 48 postings, checked live 2026-11-13 |
| Winton Group | London | greenhouse | `winton` | 7 | 1 | Greenhouse board name 'Winton', 7 postings (all London), checked live 2026-11-13 |

## Sources requiring manual intervention

### A. No website or career URL in the Excel

713 companies. The Excel describes them as direct-approach firms (FINMA or ASG register entries). To monitor one, put its career page URL in the Excel column "URL Pagina Carriere" and re-import, or add it to `config/known_sources.json`.

<details><summary>Lugano: 141</summary>

2Comply Sagl; A - Round Investment SA; A.M. Family Office SA; AITI Wealth Management (Switzerland) SA; AJ Capital Management SA; AMB PRIVATE TRUSTEE SA; AMFIN SA; AUREA Wealth Management SA; Agenda Invest; AlTi Tiedemann Global; Albula Advisors SA; Altiqa SA; Amgest SA; Aperta Fiduciaria SA; Aquila GVM Consulting SA; Arkai Swiss Trustees SA; Asfin Consult SA; Atlantinvest SA; Auriga Partners SA; Aurum Trust & Finance SA; BCO Swiss Family Office SA; BE.MAIN SA; BG Aequitum SA; Banca Aletti & C. (Suisse) SA; Banca Arner; Banca dello Stato del Cantone Ticino; Belvoir Capital AG; Berfid SA; Best Partner SA; Best Vision Solutions & Services SA; Bluesky Consulting SA; Brightside Capital SA; CIMEN ADVISOR; CO.MO.I. (Suisse) SA; CP & PARTNERS SA; Capital Finance & Bravo Company SA; Capitalsuite SA; Centro Studi Monte SA; Controlfida (Suisse) SA; Cramer Asset Management SA; Creditfinanz SA; Custodia Wealth Management SA; D&D SA; DOLFID FAMILY OFFICE SA; DVB Asset Management SA, in liquidazione; ELEUTHERIA WEALTH SA; Ephelia Capital Sagl; Equid SA; Essedi Asset Management SA; Essentia Family Office SA; Eufingest SA; Extrafid SA; FF MARCUARD SA; FGP Wealth Management SA; FGR Capital SA; FIDGEN TRUST SA; FOS4U SA; FRAME ASSET MANAGEMENT SA; FYDUCIA SA; Fairfield Capital SA; Fiduciaria Regli Sagl; Finat Gestioni SA; Fingroup Financial Management & Consulting SA; Finimex SA; Finpartner financial services SA; Finpromotion Société de Promotion Financière SA; GISEV Invest SA (GISEV Family Office); GKC Advisors SA; Graian Capital Management SA; HUTTON SA; Hafiger & Partners Asset Management SA; Harris Moor Finance SA; Helvetia Investment Advisors SA; Helvetia Trust Company SA; Helvetica Advisors SA; Henry Heyden SA; I&P Trust & Family Office SA; ICAM & PARTNERS SA; IFO International Family Office SA; ITACA SA; Intelligent Invest SA; Karimata SA; Krystal Family Office SA; LAURO & GIAVATTO SA (Pambio-Noranco); LCP Livingston Capital Partners SA; LEAG SA; LFA - Lugano Financial Advisors SA; LFG Family Office SA; LMP FINANCE SUISSE SA; Lancel International SA; Lapis Asset Management AG; Legacy CAM SA; Limfid SA; Lugano Wealth Partners SA; M&Partners Finance SA; M.E. Consulenze SA; MAFIN SA; MFA SA; Manzolini, Pedretti & Partners SA; Monti Gestione Patrimoniale SA; NORD-FIN SA; Nemesis Asset Management SA; Next Family Wealth; On Finance SA; Open Partners Asset Management SA; PER4M SA; PMP FINANZA SA; Phosphor Asset Management SA; Primus Gestione Patrimoniale SA; Privilege Ventures SA; Quantum Wealth SA (Paradiso); RGB Consulenze SA; Rexfin Asset Management SA; Rimoldi & Bergamini SA; SWIX Family Office SA; Safe & Sound Consulting SA; Safe Capital Management SA; Simgest (Family Office); Sinergia Wealth Management SA; Soave Private Investors SA; Soparfin Fiduciaria SA; Studio Commerciale Ottaviani; Sumus Capital; Suntrustee SA; TENDERCAPITAL (Suisse) SA; TFA Trade Finance Advisors SA; Talharim SA; The Niche SA; Trafida SA; UPTOVALUE ASSET MANAGEMENT SA; Unifortune Asset Management SA; V&G Trustee SA; VCI Asset Management SA; VECTOR WEALTH MANAGEMENT SA; VIRIUM Investimenti SA; Veco Invest SA; Wullschleger Martinenghi Manzini Gestione Patrimoniali SA; Wullschleger Martinenghi Manzini Trust Services SA; ZBP Asset Management SA; cm plus SA; i Partners SA

</details>

<details><summary>Geneva: 107</summary>

1788 Capital S.A.; 1875 Finance; 1959 Advisors SA; 2 PM (Suisse) SA; 3T Family Office SA; ACCURATE WEALTH MANAGEMENT SA; ACE & COMPANY SA; ADDVISION WEALTH MANAGEMENT SA; ALAF Capital SA; ALMA Family Office; ALP-GESTION.CH SA; ALYESKA ADVISORS SA; AMS - Asset Management Services (Suisse) SA; AND PRIVATE WEALTH SA; APMI - Atrium Portfolio Management and Investment SA; APPLETREE SA; AR Capital; ARCORA GESTION SA; ARILYNCH FINANCE SARL; ARODE SA; AS Investment Management SARL; ASTON CAPITAL SA; AUTHENTIC CAPITAL SA; AV Management SA; AZURA SUISSE SA; AZURE WEALTH SWITZERLAND SA; Aclon Finance SA; Actus Capital SA; Adequaris AG; Agora Capital SA; Alex Morgenbesser - Yekara; Alias Partners SA; Alkimia SA; AlphaMatrix Finance SA; Alpine Capital Partners SA; Altor Capital Management SA; Amadeus Capital SA; Amerys SA; Anaïs Ventures SA; Anchorage Services SA; Apricus Finance SA; Après-demain; Arcus Finance SA; Atlantia Wealth Management SA; Atlanticomnium SA; Atlantis Marcuard SA; Atlas Management SA; Aura Consult SA; Auris Wealth Management SA; B CAPITAL SA; B-FLEXION; BBAM SA; BBGI GROUP SA; BCT Bastion Capital & Trust SA; BERAUK Capital SA; BNP Paribas (Suisse) SA; BOCCARD & CIE FINANCE SA; BT Finance SA; Babourg Invest SA; Balboa Asset Management SA; Banque Cantonale Vaudoise (BCV); Banque Cantonale de Genève (BCGE); Banque Syz SA; Baseline Wealth Management SA; Bastions Family Office; Bauval Investment Partners SA; Bedrock SA / Bedrock Private Office SA; Berger, van Berchem & Cie SA; Black Oak Family Office; Boccard & Partenaires SA; Bruellan SA; Bruno Walter Finance SA; CA Indosuez (Switzerland) SA; CAPI SA Compagnie auxiliaire pour l'Investissement; CAPITALIA (SUISSE) SARL; Cadris SA; Capital Guidance SA; Capitalium Advisors SA; Citadel Finance SA; Coges Corraterie Gestion SA; Columbus Private; EMC Gestion de Fortune SA; FONS Family Office; Fidurhône; Geneva Asset & Wealth Management SA; Genève Invest Sàrl; HBK Investments Advisory SA (HBK Wealth); HBS SA; HELMS Family Office; La Solleille Family Office; Lida Family Office; NESS Family Office; NextGen Wealth Managers SA; Novum Partners; Numan Wealth Partners; Opal Investment Services SA; Palosanto; SERENIS SA; Sandoz Family Office; Sept Finance SA; Swissquote Bank SA; THE MATHILDE TRUST COMPANY SA; The Forum Finance Group SA; VCT Vector Gestion SA; WEDGE ASSOCIATES SA; Wibagest SA; bvo capital SA

</details>

<details><summary>Zurich: 92</summary>

21Shares AG; 3V Asset Management AG; 47 Heritage AG; ACT Asset Management AG; AMCS Asset Management & Consulting Services GmbH; AMG Analysen & Anlagen AG; AQUIS CAPITAL AG; ARR Family Office; ARTIS Partner AG; AVB Partner AG; Abaris Investment Management AG; Abegg & Co; Adventus Capital AG; Aerzte-Treuhand Finanz AG; Albin Kistler AG; Albion Capital Management Ltd.; All-In Finanz AG; Alpha Leonis Partners; Altrafin AG; Amana Family Office; Amber Lion Partners AG; Ameliora Wealth Management AG; Amergeris Wealth Management (Switzerland) AG; Aquila Associates Family Office AG; Arabella Family Office; Arboris Invest AG; Arete Ethik Invest AG; Argan AG; Armada Investment; Askfin Consulting AG; Asserta Asset Management AG; Assetmax AG; Avalor Investment AG; Axxets Management (Schweiz) AG; B & M Wealth Management AG; B&I Capital AG; BFI Infinity AG; BLZ Invest AG; BPCS Buelach Private Clients Services AG; Baryon AG; Baumgartner Family Office; Baur Family Office; Belfort Capital Group AG; Bellecapital AG; Blackfort Capital AG; Bloch Partner Vermögensverwaltungs AG; Bodewiese Cottonfield; BodmerLyhs & Partner AG; Bonnier Waldvogel & Cie AG; Braginsky Family Office; Brennwald & Partner AG; CAM Schweiz AG; Calebo Capital AG; Calibrium; Capberg Capital AG; Cape Capital AG; Colin & Cie. Schweiz AG; Eagle Invest AG; Earl Capital AG; FINAD; Gaydoul Group; Genesis Partners AG; HNW Family Office; Holliger Family Office; IHAG Holding; Invest-Partners Wealth Management AG; Investera Capital AG; Jacobs Capital; Jacobs Private Office; K Multi Family Office; KATE Family Office; Kohlmann & Co.; LIMMAT CAPITAL Alternative Investments AG; LakeStreet Family Office; Lakefield Partners; Lakeshore International; Marcuard Family Office; Meridien Family Office; Multi Family Office Zollikon; Müller-Mühl Group; Parkview; Private Office Zürichsee; RIGI Family Office; Solidum Partners AG; Sound Capital AG; VALLIEWORKS; VDB Group; Verium; WHVP AG; Woodman Asset Management AG; ecamos Capital AG; swisspartners AG

</details>

<details><summary>Dubai: 92</summary>

AFRO GROUP; AGILIS (Capital) ADVISORS; AM CAPITAL LLC; Abbey Road Investment Group; Al Maktoum Family Investment Office; Al Qasimi Family Office; Allianz Trade; Altica Partners; Amanat Holdings; Ancova Investments; Ardan Banking & Finance Consultants; Asas Capital; Averi Finance; Ayala Capital; B&F Partners Limited; BLACKHILL; BainBridge Capital Partners; Bayina Advisors; Blue Owl; COTU Ventures; Continuous Ventures; Cypher Capital; DIB Capital Ltd.; DWF Labs; Daher Investment Management; Dale Ventures F.Z.E; Dubai Future District Fund (DFDF); Dymon Asia; EQ2 Ventures; Elite Star Management Consultancies; Emirates NBD Private Banking; Enabling Future; Fairfax & Carter Capital Advisors LLC; Farro Capital; Fia Ventures; GINCO Investments; Ghaf Capital Partners; Harbins - South Asia; Hilshaw Group; Holborn Assets; ICICI Asset Management; INDEX & Cie; Iliad Partners; Investment Corporation of Dubai (ICD); Iqoniko LLC; J.P. Morgan; Jabbar Internet Group; Jade Advisors; KPMG Lower Gulf; KingsRock Advisors; Kjøller; Knuru Capital; Kuwait National Bank; LS&C Family Office; Legacy Line Family Office; Manulife; Meghraj Capital; MetaLabs Ventures; Millennium Finance Corporation; Mindshift Capital; NB Ventures; Nine Masts Capital; North Rock Capital; OBOR INVEST; Oak Hill Advisors; PIMCO; Patrimium Multi Family Office; Pearl Diver Capital; Private Department of Sheikh Mohammed Bin Khalid Al Nahyan; Qube Research and Technologies (QRT); Que Capital Limited (QueCap); RAIVEN CAPITAL; RBC; SD Capital Partners; SKH Private Family Office; Sarwa; Seed Group; Select Equity Group; Select Venture Equity; Silver Point Capital; Strategic Investment Group; Synergy Consulting, Inc.; Systema Multi Family Office; The Carling Group; Trussbridge Advisory Ltd.; UBS Wealth Management; Vy Capital; Waha Capital; Wami Capital; Wells Fargo; Welwing Capital Group; YBA Kanoo Group

</details>

<details><summary>Zug: 56</summary>

4e CAPITAL AG; ABC Consulting & Family Office; AMG Fondsverwaltung AG; AMMA Management AG; ARTER Asset Management AG; Abrias Investment Management AG; Aguaverde Family Office SA; Alpen Partners International AG; Alère Syon; Ammer Capital; Apex Asset Management; Apollon Wealth AG; Argentière Capital AG; Aspis Capital Solutions GmbH; Atrium Family Office AG; Ayaltis AG; B-R & H Finance SA; BALLY CAPITAL ADVISORS AG; Bluerain Partners Group; Broch Family Office; COFRA Holding; CSF Family Office; Captiva Family Office; Cartesian AG; Corestone Investment Managers; Emcore Asset Management AG; Empira Group; Ermes Wealth Management; Family Office 360grad; GT Family Office; Genico Family Office; HP Wild Family Office; Hammer Team; Kendris; M. & A. GLOOR Family Office; Mayfair Asset Management; NVA Family Office; PG3; PWA Family Office; Pillar Capital AG; QCAM Currency Asset Management AG; RichmondGate Family Office; S&P Family Office; SAYANO Family Office; Scipio Family Office; Silence Family Office; Studer Family Office; Treubera Family Office; U.I. Bettemann Family Office; Vermar; Victoria Family Office; WINVEST ASSET MANAGEMENT AG; Wille Finance; Wollerau Family Office; Woodman Family Office; d-tail Family Office

</details>

<details><summary>London: 54</summary>

01 Capital; 23 Capital; 24Haymarket; 3i Group; 4BIO Capital; 72 Capital; 7percent Ventures; 8 Miles LLP; ACF Investment Bank; Acoro Capital Partners; Adelpha Group; Advent International; Air Street Capital; Aladdin Capital Management; Alaris Corporate Finance; Aldebrook Finance; Alfred Henry Corporate Finance; Amadeus Capital Partners; Amplitude Capital; Antipodes; Aquaa Partners; Arcapita; Arcus Infrastructure Partners; Arkios Corporate Finance; Artemis Fund Managers; BGF; Baird Capital Partners Europe; Bank of America; Basalt Infrastructure Partners; Bemberg Capital; Blue Earth Capital; CVC Credit; Citi; Deutsche Bank; Episode 1 Ventures; Foresight Group; Harris Williams; Headway Capital Partners; Helios Investment Partners; JPMorgan; Literacy Capital; Morgan Stanley; North Asset Management; One Peak; Pears Partnership Capital; Perwyn; Polar Capital; Schroders Capital; Smedvig Ventures; Soditic Asset Management; Squarepoint Ops; Two Sigma International; Weybourne Partners; William Blair

</details>

<details><summary>Sydney: 53</summary>

Acorn Capital; Ad Astra Corporate Advisory; Adamantem Capital; Airtree Ventures; Allier Capital; Alphinity Investment Management; Antipodes Partners; App Securities; Artesian VC; Bennelong Capital; Blackbird Ventures; Blackpeak Capital; BlueRock; BurnVoir Corporate Finance; Canary Capital; Canterbury Hill Advisory; Capital Edge Corporate Advisory; Citigroup; Coastal Fund; Ellerston Capital; Five V Capital; Flagstaff Partners; Goldman Sachs; Grant Samuel; Grant Thornton; Gresham; HMC Capital Partners; Henslow; Highbury Partnership; ICA Partners; Ironbark Asset Management; Jarden; Jefferies; Lazard Australia; Luminis Partners; MA Moelis Australia; MLC Asset Management; Macquarie Asset Management (PE division); Macquarie Capital; Main Sequence Ventures; OneVentures; Pacific Equity Partners; Pemba Capital Partners; Platinum Asset Management; ProSolution Private Office; Quadrant Private Equity; Qube (Sydney office); Rothschild; Sapien Ventures; Tenmile; Viridian Financial Group; Wilson Pateras; Yarra Capital Management (con Tyndall Asset Management)

</details>

<details><summary>Luxembourg: 52</summary>

4IP Fund Management; A Capital Management; AIF Management Services; ALCEDA Fund Management; ALFIN Luxembourg; ANDBANC Asset Management Luxembourg; AXA Funds Management; Aberdeen Investment Services; Acolin Fund Management; Aegon Asset Management Luxembourg; Alken Luxembourg; Allium; Anphiko Asset Management; Antea Advisory; Artas Advisory; Augemus; Augur Capital; Axon Advisory & Consulting; Axxion; B&R Consulting; Banque Transatlantique Luxembourg SA; Batipart Invest; BlueBay Funds Management Company; C&D Investments; CBP Quilvest; CME Financial Services; CapFields; Cee Cat; Core Capital Management; Cube Infrastructure Fund; Delfin S.à r.l. (Del Vecchio family office); ESPERIA Luxembourg; Edifice Capital; Engelwood Asset Management; Eurinvest Partners; Eventus Fondsverwaltung; FWU Invest; Fisher Investments Luxembourg; Genii Capital; IFG Capital; IK Partners; Luxembourg Financial Group; Luxempart; Luxtrust; Novator Partners Family Office; OTP Global Funds; SILVER GROUP ADVISORY; Standish Management (Luxembourg); TNN Capital; The Carlyle Group; Ziffer Group; theCatalysts

</details>

<details><summary>Basel: 36</summary>

ALTOR Vermögensverwaltung AG; ATAG Family Office; AWT Investment AG; AZETA SA; AarauInvest AG; Alban Basel GmbH; Aldred & Cie. Family Office; Allegra Vermögensverwaltungs AG; Alpha Asset Administration AG; Anderes Finanzberatung AG; Arabella Vermögensverwaltung AG; Aran Wealth AG; Astrantia AG; Avestum AG; B&G Consulting SA; BCO Vermögensverwaltung AG; BM Swiss Performance AG; Baltrag AG; Bank CIC (Schweiz) AG; Bank J. Safra Sarasin AG; Basler Kantonalbank; Belvédère Asset Management AG; BentinPartner GmbH; Blickenstorfer & Bacchini AG; Bächli & Partner AG; Bühler Vermögensverwaltung AG; Ehinger & Cie.; Fortea Family Office; Jeannet Family Office; LGT Bank (Schweiz) AG; Nievergelt & Stoehr Family Office; PCS Holding; Sayn-Wittgenstein Family Office; Spectrum Value Management; Swiss KMU Partners; infinitas capital

</details>

<details><summary>Melbourne: 16</summary>

Alphinity; Banksia Capital; Bell Potter (corporate advisory); Canterbury Partners; Drummond Capital Partners; First Guardian Capital; Fleet Asset Management; Harbury Advisors; Hostplus (VC/PE allocation); IFM Investors Private Equity; K2 Asset Management; L1 Capital (hedge fund/VC); M&A Partners; Miles Advisory Partners; New Holland Capital; Viburnum Funds

</details>

<details><summary>Perth: 13</summary>

Alto Capital; Canaccord Genuity Group; Chieftain Securities; Futures Fund; Grange Consulting; Longreach Capital; Modus Capital; Ocean Reach Advisory; Seed Growth IM; Sternship Advisers; Vert Capital; Yuuwa Capital; Zephyr Capital

</details>

<details><summary>Milan: 1</summary>

Associazione Italiana Private Banking (AIPB)

</details>

### B. Recognised system without a connector, or page not machine-readable

None yet. This list fills in as the discovery step analyses career pages.


### C. Waiting for automatic analysis (585)

No action needed: the daily workflow analyses these pages (set the first run to 600). Listed so that nothing is silently left out.

<details><summary>Show the list</summary>

| Company | Offices | Page |
|---|---|---|
| 21 Invest | Milan | https://www.21invest.com/contact |
| 360 Capital | Milan | https://www.360capital.com/contact |
| ADEPA Asset Management | Luxembourg | https://www.adepa.com/careers |
| AITi Tiedemann Global | Dubai | https://www.aitiglobal.com/careers |
| AKO Capital | London | https://akocapital.com |
| Abts & Partners S.A. | Luxembourg | https://www.abtspartners.com/en/contact |
| Accenture Song | Lugano | https://www.accenture.com/ch-en/careers |
| Accuracy | Milan | https://www.accuracy.com/careers |
| AcomeA SGR | Milan | https://www.acomea.it/lavora-con-noi |
| Aditum Investment Management | Dubai | https://www.aditumim.com |
| Advent International Luxembourg S.à r.l. | Luxembourg | https://www.adventinternational.com/careers |
| AfricInvest | Dubai | https://www.africinvest.com/careers |
| Aksìa SGR | Milan | https://www.aksia.com/contatti |
| Al Ghurair Investment | Dubai | https://www.alghurair.com/en/careers |
| Al Mal Capital PSC | Dubai | https://www.almalcapital.com/careers |
| Al-Futtaim Group Investments | Dubai | https://www.alfuttaim.com/careers |
| Alantra | London, Milan | https://www.alantra.com/talent |
| AlbionVC | London | https://albion.vc/careers |
| Alexa Capital | London | https://alexacapital.com |
| Algebris Investments | London, Milan | https://www.algebris.com/careers |
| AlixPartners | Dubai, London, Milan | https://www.alixpartners.com/careers |
| Allianz Global Investors (succursale Lussemburgo) | Luxembourg | https://www.allianzgi.com/en/careers |
| Alpen Capital | Dubai | https://www.alpencapital.com/careers.html |
| Alpha Patrimoine S.A. | Luxembourg | https://www.alphapatrimoine.lu/contact |
| Alquity Investment Management (Lux) | Luxembourg | https://www.alquity.com/contact-us |
| Alter Domus Luxembourg S.à r.l. | Luxembourg | https://www.alterdomus.com/careers |
| Alto Partners SGR | Milan | https://www.altopartners.it/contatti |
| Altum Management Company S.A. | Luxembourg | https://altumgroup.com/careers/ |
| Altum Management Sàrl | Luxembourg | https://altumgroup.com/careers/ |
| Alvarez & Marsal | Dubai, London, Milan | https://www.alvarezandmarsal.com/careers |
| Alvarez & Marsal Luxembourg S.à r.l. | Luxembourg | https://www.alvarezandmarsal.com/careers |
| Amber Capital Italia SGR | Milan | https://www.ambercapital.com/contact |
| Ambienta SGR | Milan | https://ambientasgr.com/careers |
| Amundi | Luxembourg, Milan | https://www.amundi.it/investitori-privati/carriere |
| Amwal Capital Partners | Dubai | https://www.amwalcapital.com |
| Anima | Milan | https://www.animasgr.it/IT/gruppo/Pagine/Lavora-con-noi.aspx |
| Anthilia Capital Partners SGR | Milan | https://www.anthilia.it/contatti |
| Apax Partners | London | https://apax.com/careers |
| Apex Fund Services S.A. | Luxembourg | https://www.apexgroup.com/careers |
| Aquila Capital (Aquila Group Lux) | Luxembourg | https://www.aquila-capital.de/en/career |
| Arbuthnot Latham | London | https://arbuthnotlatham.co.uk/careers |
| Arca Fondi SGR | Milan | https://www.arcafondi.it/lavora-con-noi |
| Arche Associates S.A. (Arche FO) | Luxembourg | https://www.arche-associates.com/contact |
| Arcmont Asset Management | London | https://arcmont.com/careers |
| Ardian Italy | Milan | https://www.ardian.com/en/careers |
| Arendt & Medernach SA | Luxembourg | https://www.arendt.com/careers/our-recruitment-process/ |
| Argonaut | Perth | http://www.argonaut.com/ |
| Argonaut Funds Management Pty Ltd | Perth | http://argonautfundsmanagement.com/ |
| Arkios Italy | Milan | https://www.arkios.it/lavora-con-noi |
| Arma Partners | London | https://armapartners.com/careers |
| Arqaam Capital | Dubai | https://www.arqaamcapital.com/careers |
| Arthur D. Little | Milan | https://www.adlittle.com/en/careers |
| Arthur D. Little Middle East | Dubai | https://www.adlittle.com/en/careers |
| Asante Capital Group | London | https://asantecapital.com/careers |
| Ashmore Group Middle East | Dubai | https://www.ashmoregroup.com/careers |
| Aspect Capital | London | https://aspectcapital.com/careers |
| Astorg Asset Management S.à r.l. | Luxembourg | https://www.astorg.com/careers |
| Atomico | London | https://atomico.com/careers |
| Atomo Sicav / Lemanik Desk Italia | Luxembourg | https://www.lemanikgroup.com/careers |
| August Equity | London | https://augustequity.com |
| Augusta & Co | London | https://augustaco.com/careers |
| Axion Swiss Bank SA | Lugano | https://www.axionbank.ch/ |
| Azimut (ME) Limited | Dubai | https://www.azimut-group.com/en/careers |
| Azimut (inclusa Azimut Corporate Finance) | Milan | https://www.azimut.it/lavora-con-noi |
| Azimut Investments S.A. | Luxembourg | https://www.azimut.it/lavora-con-noi |
| Azimut Switzerland SA (AZ Swiss) | Lugano | https://www.azswiss.ch/ |
| Aztec Financial Services (Lux) S.A. | Luxembourg | https://www.aztecgroup.co.uk/careers |
| Azure Capital | Perth, Sydney | http://www.azurecapital.com.au/ |
| BC Partners | London, Luxembourg, Milan | https://www.bcpartners.com/contact |
| BCEE Asset Management | Luxembourg | https://www.spuerkeess.lu/en/about-us/careers |
| BCG | London | https://careers.bcg.com |
| BDO Corporate Finance (Middle East) LLP | Dubai | https://www.bdo.ae/en-gb/careers |
| BDO Italia | Milan | https://www.bdo.it/it-it/carriere |
| BDO Luxembourg | Luxembourg | https://www.bdo.lu/en-gb/careers |
| BDO UK (Advisory) | London | https://bdocareers.co.uk |
| BECO Capital | Dubai | https://www.becocapital.com/careers |
| BFF Bank | Milan | https://it.bff.com/it/careers |
| BG (Suisse) Private Bank SA | Lugano | https://www.bgsuisse.ch/ |
| BGH Capital | Melbourne | http://www.bghcapital.com/ |
| BIP Investment Partners | Luxembourg | https://www.bip.lu/contact |
| BL Advisory / Boreal Partners | Luxembourg | https://www.bl-advisory.com |
| BLI - Banque de Luxembourg Investments | Luxembourg | https://www.bli.lu/en/careers |
| BNY Mellon SA/NV, Luxembourg Branch | Luxembourg | https://www.bnymellon.com/us/en/careers.html |
| Baillie Gifford (London Office) | London | https://earlycareers.bailliegifford.com |
| Bain | London | https://bain.com/careers |
| Bain & Company | Milan | https://www.bain.com/it/carriere |
| Bain & Company Middle East | Dubai | https://www.bain.com/careers |
| Baker Tilly Luxembourg | Luxembourg | https://www.bakertilly.lu/en/careers |
| Balderton Capital | London | https://balderton.com/careers |
| Balyasny | Dubai | https://www.bamfunds.com/careers |
| Balyasny Asset Management UK | London | https://bamfunds.com/careers |
| Banca Akros | Milan | https://gruppobancobpm.it/lavora-con-noi/ |
| Banca Aletti | Milan | https://gruppo.bancobpm.it/carriere |
| Banca Credinvest SA | Lugano | https://www.credinvest.ch/ |
| Banca Euromobiliare | Milan | https://www.credem.it/content/credem/it/gruppo-credem/carriere.html |
| Banca Finint | Milan | https://www.bancafinint.com/it/carriere |
| Banca Generali | Milan | https://www.bancagenerali.com/carriere |
| Banca Investis | Milan | https://www.bancainvestis.com/lavora-con-noi |
| Banca Popolare di Sondrio (Suisse) SA | Lugano | https://www.bps-suisse.ch/it/H05/lavorare-in-bps-suisse |
| Banca Privata Edmond de Rothschild Lugano SA | Lugano | https://www.edmond-de-rothschild.com/en/careers |
| Banca Profilo | Milan | https://www.bancaprofilo.it/lavora-con-noi |
| Banca WIR | Lugano | https://www.wir.ch/ |
| Banca Zarattini & Co. SA | Lugano | https://www.zarattinibank.ch/ |
| Banca del Ceresio S.A. | Lugano | https://www.ceresioinvestors.com/en/contatti.html |
| Banca del Sempione SA | Lugano | https://www.bancasempione.ch/ |
| Bank Julius Baer Europe S.A. | Luxembourg | https://www.juliusbaer.com/en/careers |
| Banor SIM | Milan | https://www.banor.it/lavora-con-noi |
| Banque Cramer & Cie SA | Lugano | https://www.banquecramer.ch/ |
| Banque Internationale à Luxembourg (BIL) | Luxembourg | https://careers.bil.com |
| Banque Internationale à Luxembourg (Suisse) SA | Lugano | https://www.bil.com/ |
| Banque de Luxembourg S.A. | Luxembourg | https://www.banquedeluxembourg.com/en/bank/corporate/careers |
| Barclays | Dubai, London | https://search.jobs.barclays |
| Baringa Partners | London | https://baringa.com/en/careers |
| Baron Capital Management | Dubai | https://www.baroncapitalgroup.com/careers |
| Barrenjoey | Perth, Sydney | https://barrenjoey.com/careers/ |
| Bellatrix Asset Management | Luxembourg | https://www.bellatrix.lu/en/contact |
| Bellevue Asset Management | Zurich | https://www.bellevue.ch |
| Berenberg (London Branch) | London | https://berenberg.de/en/careers |
| BlackRock | London, Zurich | https://careers.blackrock.com/ |
| BlackRock (Luxembourg) S.A. | Luxembourg | https://careers.blackrock.com |
| BlackRock Italy | Milan | https://careers.blackrock.com |
| Blackstone Europe Fund Management S.à r.l. | Luxembourg | https://www.blackstone.com/careers |
| BlueCrest Capital | Dubai | https://www.bluecrestcapital.com |
| BlueOrchard Finance (Lux Entity) | Luxembourg | https://www.blueorchard.com/about-us/careers |
| BlueStar Investment Managers SA | Lugano | https://www.bluestar-im.ch/ |
| Borletti Group | Luxembourg, Milan | https://www.borlettigroup.com/contact |
| Boston Consulting Group (BCG) | Dubai, Milan | https://careers.bcg.com |
| Bowmark Capital | London | https://bowmark.com |
| Brevan Howard | Dubai, London, Luxembourg | https://brevanhoward.com/careers |
| Bridgepoint | London | https://bridgepoint.eu/careers |
| Brook Asset Management (ex Odey) | London | https://brookam.com |
| Brookfield Asset Management | Dubai | https://www.brookfield.com/careers |
| Brown Brothers Harriman (Lux) S.C.A. | Luxembourg | https://www.bbh.com/us/en/careers.html |
| Bär & Karrer SA | Lugano | https://www.baerkarrer.ch/en/career/jobs/open-positions |
| C. Hoare & Co. | London | https://hoaresbank.co.uk/careers |
| CA Indosuez Finanziaria SA | Lugano | https://ch.indosuez.com/ |
| CA Indosuez Wealth (Europe) | Luxembourg | https://www.ca-indosuez.com/careers |
| CACEIS Bank, Luxembourg Branch | Luxembourg | https://www.caceis.com/careers |
| CDP Venture Capital SGR | Milan | https://www.cdpventurecapital.it/lavora-con-noi |
| CIR (Compagnie Industriali Riunite) | Milan | https://www.cirgroup.it/contatti |
| COIMA SGR | Milan | https://www.coima.com/it/contatti/lavora-con-noi |
| CQS (Manulife CQS) | London | https://cqs.com/careers |
| CSC Global Financial Markets (ex Intertrust) | Luxembourg | https://www.cscglobal.com/service/careers |
| CVC (ufficio londinese) | London | https://cvc.com/careers |
| CVC Capital Partners | Dubai, Luxembourg, Milan | https://www.cvc.com/careers |
| Cadogan | London | https://cadogan.co.uk/careers |
| Caledonia Investments | London | https://caledonia.com/careers |
| Campbell Lutyens | London | https://campbell-lutyens.com/careers |
| Candriam Italia | Milan | https://www.candriam.com/en/careers |
| Candriam Luxembourg | Luxembourg | https://www.candriam.com/en/professional/careers |
| Capital Dynamics Holding AG | Zug | https://www.capdyn.com/careers/ |
| CapitalatWork Foyer Group S.A. | Luxembourg | https://www.capitalatwork.com/en-lu/jobs |
| Capula Investment Management | London | https://capulaglobal.com/careers |
| Capvis | Zug | https://www.capvis.com |
| Carmignac | Milan | https://www.carmignac.com/en/careers |
| Carmignac Gestion Luxembourg S.A. | Luxembourg | https://www.carmignac.lu/en_GB/careers |
| Carne Global Fund Managers (Lux) S.A. | Luxembourg | https://www.carnegroup.com/careers |
| Carthesio SA | Lugano | https://www.carthesio.com/ |
| Cassa Lombarda | Milan | https://www.cassalombarda.it/lavora-con-noi |
| Cassiopea Partners | Milan | https://www.cassiopeapartners.com/contact-us |
| Castello SGR | Milan | https://www.castellosgr.com/lavora-con-noi |
| Cavendish Financial | London | https://cavendish.com/careers |
| Centerview Partners | London | https://centerviewpartners.com/careers.aspx |
| Centralis Group | Luxembourg | https://www.centralisgroup.com/careers |
| Charme Capital Partners SGR | Milan | https://www.charmecapitalpartners.com/contact |
| Chenavari Credit Partners (Lux) | Luxembourg | https://www.chenavari.com/careers |
| Cherry Bank (Divisione Milano) | Milan | https://www.cherrybank.it/lavora-con-noi |
| Cheyne Capital | London | https://cheynecapital.com/careers |
| Cinven | London, Luxembourg | https://cinven.com/careers |
| Citadel (Europe) | London | https://citadel.com/careers |
| Citco Fund Services (Luxembourg) S.A. | Luxembourg | https://www.citco.com/careers |
| Cité Gestion | Lugano | https://www.cite-gestion.com/ |
| Clairfield International (Equita K Finance) | Milan | https://www.clairfield.com/careers |
| Clearwater International | London, Milan | https://www.clearwatercf.com/careers |
| Clessidra Group | Milan | https://www.clessidragroup.it/contatti |
| Clipperton (London) | London | https://clipperton.com/careers |
| Close Brothers Group | London | https://closebrothers.com/careers |
| Cobepa (Lux Entity) | Luxembourg | https://www.cobepa.com/contact |
| Coller Capital | London | https://collercapital.com/careers |
| Colombo Wealth SA | Lugano | https://www.colombowealth.com/ |
| CompAM Fund / Compass AM (Lux) | Luxembourg | https://www.compass-am.com |
| Connaught | London | https://connaught.co |
| Consilium SGR | Milan | https://www.consiliumsgr.it/contatti |
| Conventum TPS (Gruppo HAL) | Luxembourg | https://www.hal-privatbank.com/karriere |
| Copernico SIM | Milan | https://www.copernicosim.com/lavora-con-noi |
| Copernicus (Family Office / Asset Management) | Lugano | https://www.copernicuswm.com/ |
| Copernicus Asset Management SA | Lugano | https://www.copernicuswm.com/ |
| Cordusio SIM | Milan | https://www.unicreditgroup.eu/en/careers.html |
| Cornèr Banca SA | Lugano | https://www.corner.ch/it/chi-siamo/lavorare-in-corner/ |
| Coutts & Co | London | https://coutts.com/careers |
| Creatrust S.à r.l. | Luxembourg | https://www.creatrust.com/jobs-career |
| Creek Capital | Dubai | https://www.creekcapital.com |
| Cross Border | Milan | https://www.crossborder.it/contatti |
| Crossinvest | Lugano, Milan | https://www.crossinvest.ch/it/carriere |
| DC Advisory | London, Milan | https://www.dcadvisory.com/careers |
| DWS Investment S.A. | Luxembourg | https://careers.dws.com |
| Dalma Capital | Dubai | https://www.dalmacapital.com/careers |
| Daman Investments | Dubai | https://www.daman.ae/careers |
| DeA Capital | Milan | https://www.deacapital.com/ |
| DeA Capital Real Estate SGR | Milan | https://www.deacapitalre.com/lavora-con-noi |
| Degroof Petercam Asset Services (DPAS) | Luxembourg | https://www.degroofpetercam.com/en-lu/careers |
| Deloitte | Dubai, London, Luxembourg, Melbourne, Milan, Perth, Sydney, Zurich | https://www.deloitte.com/ch/en/careers.html |
| Deutsche Numis | London | https://dbnumis.com/careers |
| Dynasty Asset Management S.A. | Luxembourg | https://www.dynasty-am.lu/contact |
| ECI Partners | London | https://ecipartners.com/about/join-us |
| EFG Bank (Luxembourg) S.A. | Luxembourg | https://www.efgbank.com/careers |
| EFG Bank (inclusa ex BSI) | Lugano | https://www.efginternational.com/careers |
| EFG Hermes (UAE) | Dubai | https://www.efghermes.com/en/careers |
| EFG International (inclusa ex BSI) | Zurich | https://www.efginternational.com/careers |
| EFG Private Bank | London | https://efgbank.co.uk/careers |
| EQT | London, Luxembourg | https://www.eqtgroup.com/careers |
| EQUITA | Milan | https://www.equita.eu/it/careers.html |
| EY | Dubai, London, Luxembourg, Melbourne, Milan, Perth, Sydney | https://www.ey.com/it_it/careers |
| EY-Parthenon (London) | London | https://ey.com/en_uk/careers/ey-parthenon |
| Eastbridge Group | Luxembourg | https://www.eastbridgegroup.com/contact |
| Eastspring Investments (Luxembourg) S.A. | Luxembourg | https://www.eastspring.com/careers |
| Edizione | Milan | https://www.edizione.com/en/contacts |
| Edmond de Rothschild | Milan | https://www.edmond-de-rothschild.com/en/careers |
| Edmond de Rothschild (Europe) S.A. | Luxembourg | https://www.edmond-de-rothschild.com/en/careers |
| Egerton Capital | London | https://egertoncapital.com |
| Eight Advisory | Milan | https://www.8advisory.com/en/careers |
| Eisler Capital | Dubai, London | https://eislercapital.com/careers |
| Emirates NBD Capital | Dubai | https://www.emiratesnbd.com/en/careers |
| Engelhart (ECTP) | Dubai | https://www.ectp.com/careers |
| Entangled Capital SGR | Milan | https://www.entangledcapital.com/contatti |
| Ento Capital | Dubai | https://www.entocapital.com |
| Ersel Banca Privata | Milan | https://www.ersel.it/it/lavora-con-noi |
| Ethenea Independent Investors S.A. | Luxembourg | https://www.ethenea.com/careers |
| Ethica Group | Milan | https://www.ethicagroup.it/lavora-con-noi |
| Eurizon | Milan | https://www.intesanpaolo.com/it/careers.html |
| Eurizon Capital S.A. | Luxembourg | https://www.eurizoncapital.com/it-IT/carriere |
| Euromobiliare AM SGR | Milan | https://www.eurosgr.it/lavora-con-noi |
| Europa Partners | London | https://europapartners.com |
| European Capital Partners | Luxembourg | https://www.ecp.lu/contact |
| European Investment Fund (EIF) | Luxembourg | https://www.eib.org/en/about/careers |
| Evercore | London | https://evercore.com/careers |
| Evercore Partners | Dubai | https://www.evercore.com/careers |
| ExodusPoint Capital Management | Dubai | https://www.exoduspoint.com/careers |
| Expon Capital S.à r.l. | Luxembourg | https://www.expon.vc/contact |
| Exponent Private Equity | London | https://exponentpe.com |
| F2i SGR | Milan | https://www.f2isgr.it/lavora-con-noi |
| FIA Asset Management | Luxembourg | https://www.fia.lu/contact |
| FIL Investment Management (Fidelity) | Luxembourg | https://careers.fidelityinternational.com |
| FIM Partners | Dubai | https://www.fimpartners.com/careers |
| FRP Advisory | London | https://frpadvisory.com/careers |
| FSI SGR (Fondo Strategico Italiano) | Milan | https://www.fondostrategico.it/contatti |
| FTI Consulting | Dubai, London, Milan | https://www.fticonsulting.com/careers |
| Fajr Capital | Dubai | https://www.fajrcapital.com/careers |
| Fenchurch Advisory Partners | London | https://fenchurchadvisory.com/careers |
| Fidelity International | Milan | https://careers.fidelityinternational.com |
| Fideuram ISPB | Milan | https://group.intesasanpaolo.com/it/careers |
| Fidinam SA | Lugano | https://www.fidinam.com/it/carriera |
| Fiera Capital (MEA) | Dubai | https://www.fieracapital.com/en/careers |
| Financière de l'Échiquier (LFDE) | Milan | https://www.lfde.com/it-it/carriere |
| Findlay Park Partners | London | https://findlaypark.com |
| Fineurop Soditic | Milan | https://www.fineuropsoditic.com/contatti |
| Finimmo (Ulfia Group) | Luxembourg | https://www.finimmo.lu/en/careers |
| Finint Investments SGR | Milan | https://www.bancafinint.com/it/carriere |
| Fininvest | Milan | https://www.fininvest.it/it/lavora-con-noi |
| First Abu Dhabi Bank (FAB) | Dubai | https://www.bankfab.com/en-ae/careers |
| First Capital | Milan | https://www.firstcapital.it/contatti |
| Flossbach von Storch Invest S.A. | Luxembourg | https://www.flossbachvonstorch.lu/de/karriere |
| Fondo Italiano d'Investimento SGR | Milan | https://www.fondoitaliano.it/lavora-con-noi |
| Forvis Mazars | Milan | https://www.forvismazars.com/it/it/carriere |
| Forvis Mazars Luxembourg | Luxembourg | https://www.forvismazars.com/lu/en/careers |
| Franklin Templeton Int. Services S.à r.l. | Luxembourg | https://www.franklintempletoncareers.com |
| Franklin Templeton Italia | Milan | https://www.franklintempletoncareers.com |
| Franklin Templeton ME | Dubai | https://www.franklintempleton.com/careers |
| Fuchs & Associes Finance | Luxembourg | https://www.wize.lu/careers |
| FundRock Management Company S.A. | Luxembourg | https://www.fundrock.com/careers |
| G-Research | London | https://gresearch.com/vacancies |
| GP Bullhound | London | https://gpbullhound.com/careers |
| GSA Capital | Dubai | https://www.gsacapital.com/careers |
| Garnell | Milan | https://www.garnell.it/lavora-con-noi |
| Gate Capital | Dubai | https://www.gatecapital.net |
| General Atlantic | Dubai | https://www.generalatlantic.com/careers |
| Generali Investments | Milan | https://www.generali-investments.com/it/it/careers |
| Generali Investments Luxembourg S.A. | Luxembourg | https://www.generali-investments.com/careers |
| Gladstone Capital Management | London | https://gladstonecapital.com |
| Gleacher Shacklock | London | https://gleachershacklock.com/careers |
| Global Ventures | Dubai | https://www.global.vc/careers |
| Golding Capital Partners (Lux) S.à r.l. | Luxembourg | https://www.goldingcapital.com/en/career |
| Goldman Sachs Asset Management | Milan | https://www.goldmansachs.com/careers |
| Goldman Sachs International | London | https://www.goldmansachs.com/careers/students |
| Goldman Sachs International Service Entities Holdings Limited | London | https://www.goldmansachs.com/careers/students |
| Gradiente SGR | Milan | https://www.gradientesgr.it/contatti |
| Grant Thornton - UAE | Dubai | https://www.grantthornton.ae/careers |
| Grant Thornton Financial Advisory | Milan | https://www.grantthornton.it/carriere |
| Grant Thornton Luxembourg | Luxembourg | https://www.grantthornton.lu/en/careers |
| Grant Thornton UK | London | https://grantthornton.co.uk/careers |
| Graphite Capital | London | https://graphitecapital.com |
| Green Arrow | Milan | https://www.greenarrowcapital.com/ |
| Green Horse Advisory | Milan | https://www.greenhorse.it/careers |
| Greenhill & Co. (Mizuho) | London | https://greenhill.com/careers |
| Grosvenor | London | https://grosvenor.com/careers |
| Gulf Capital | Dubai | https://www.gulfcapital.com/careers |
| Gulf Islamic Investments (GII) | Dubai | https://www.gii.ae/careers |
| H14 | Milan | https://www.h14.com/contact |
| HACA Partners | Luxembourg | https://www.hacapartners.com/contact |
| HAT SGR | Milan | https://www.hatsgr.com/contatti |
| HG Capital (Hg) | London | https://hgcapital.com/careers |
| HSBC Bank plc | London | https://hsbc.com/careers |
| HSBC Private Bank (Suisse) SA | Geneva | https://www.hsbc.com/careers |
| Habib Bank AG Zurich (HBZ) | Dubai | https://www.habibbank.com/careers |
| Hampden & Co | London | https://hampdenandco.com/careers |
| Hauck & Aufhäuser Fund Services S.A. | Luxembourg | https://www.hal-privatbank.com/karriere |
| Hayfin Capital Management | London | https://hayfin.com/careers |
| Hedge Invest SGR | Milan | https://www.hedgeinvest.it/contatti |
| Hinduja Bank (Switzerland) Ltd | Lugano | https://www.hindujabank.com/ |
| Hollyport Capital | London | https://hollyportcapital.com/careers |
| Hottinger & Co | London | https://hottinger.co.uk |
| Houlihan Lokey | London, Milan | https://www.hl.com/about-us/careers |
| Houlihan Lokey MEA | Dubai | https://www.hl.com/careers |
| Hudson Bay | Dubai | https://www.hudsonbaycapital.com/careers |
| Hyphen-Group | Lugano | https://www.hyphen-group.com/ |
| ICG (Intermediate Capital Group) | London | https://icgam.com/careers |
| IFM Investors | Melbourne | https://www.ifminvestors.com/en-au/careers/ |
| IQ-EQ Luxembourg S.A. | Luxembourg | https://www.iqeq.com/careers |
| Indaco Venture Partners SGR | Milan | https://www.indacosgr.com/contact |
| Index Ventures (London) | London | https://indexventures.com/careers |
| Inflexion Private Equity | London | https://inflexion.com/careers |
| Intermonte | Milan | https://www.intermonte.it/carriere |
| Interpath Advisory | London | https://interpathadvisory.com/careers |
| Intesa Sanpaolo IMI Corporate & Investment Banking | Milan | https://group.intesasanpaolo.com/it/careers |
| Intesa Sanpaolo Wealth Management (Lux) | Luxembourg | https://www.intesasanpaolowealthmanagement.lu/en/careers |
| Invesco Italia | Milan | https://www.invesco.com/corporate/en/careers.html |
| Investec Bank plc | London | https://investec.com/en_gb/welcome-to-investec/careers.html |
| Investindustrial | Milan | https://www.investindustrial.com/careers |
| Invision Asset Management AG | Zug | https://www.invision.ch/en/ |
| Itago SGR | Milan | https://www.itagosgr.it/contatti |
| Italmobiliare | Milan | https://www.italmobiliare.it/it/carriere |
| J.P. Morgan Asset Management | Milan | https://www.jpmorganchase.com/careers |
| JAB Holding Company S.à r.l. | Luxembourg | https://www.jabholdco.com/contact |
| JPMorgan Asset Management (Europe) S.à r.l. | Luxembourg | https://www.jpmorganchase.com/careers |
| Jamieson Corporate Finance | London | https://jamiesoncf.com |
| Janus Henderson EM PE (ex NBK CP) | Dubai | https://www.nbkcapitalpartners.com |
| Jefferies International | London | https://jefferies.com/careers |
| Jefferies MENA | Dubai | https://www.jefferies.com/careers |
| Julius Baer | Dubai, Lugano, Zurich | https://www.juliusbaer.com/en/careers/ |
| Jupiter Asset Management | London | https://jupiteram.com/uk/en/corporate/careers |
| KBW Investments | Dubai | https://www.kbw-investments.com |
| KPMG | London, Luxembourg, Melbourne, Milan, Perth, Sydney | https://kpmg.com/it/it/home/careers.html |
| Kairos | Milan | https://www.kairospartners.com/carriere/ |
| Kamco Invest UAE | Dubai | https://www.kamcoinvest.com/careers |
| Kartesia Management S.à r.l. | Luxembourg | https://www.kartesia.com/careers |
| Kearney | Milan | https://www.kearney.com/careers |
| Kearney Middle East | Dubai | https://www.kearney.com/careers |
| Kepler Cheuvreux | Milan | https://www.keplercheuvreux.com |
| King Street Capital Management | Dubai | https://www.kingstreet.com/careers |
| Kintbury Capital | London | https://kintburycapital.com |
| Kitra Advisory S.p.a. | Milan | https://www.kitra-advisory.com/ |
| Klecha & Co. | Milan | https://www.klecha-co.com/careers |
| Kleinwort Hambros | London | https://kleinworthambros.com/en/careers |
| Kroll | Dubai, London, Milan | https://www.kroll.com/en/careers |
| Kryalos SGR | Milan | https://www.kryalossgr.com/lavora-con-noi |
| L&B Partners | Milan | https://www.lbpartners.net/careers |
| L.E.K. Consulting | Dubai, London | https://lek.com/careers |
| LFG + Zest SA | Lugano | https://www.lfgzest.com/ |
| LGT Capital Partners | Pfaeffikon | https://www.lgtcp.com |
| Langham Hall Luxembourg S.à r.l. | Luxembourg | https://www.langhamhall.com/careers |
| Lansdowne Partners | London | https://lansdownepartners.com |
| Lazard | London | https://lazard.com/careers |
| Lazard Financial Advisory | Dubai | https://www.lazard.com/careers |
| Lazard Italia | Milan | https://www.lazard.com/careers |
| Legal & General Investment Management (LGIM) | London | https://lgim.com/uk/en/careers |
| Lemanik Asset Management S.A. | Luxembourg | https://www.lemanikgroup.com/careers |
| Leonteq | Zurich | https://www.leonteq.com |
| Levant Capital | Dubai | https://www.levantcapital.com |
| Liberty Corporate Finance | London | https://libertycf.com |
| Lighthouse Canton | Dubai | https://www.lighthouse-canton.com/careers |
| Limestone Platform AS (Lux Branch) | Luxembourg | https://www.limestone.eu/contact |
| Lincoln International | London, Milan | https://www.lincolninternational.com/careers |
| Livingbridge | London | https://livingbridge.com/careers |
| Livingstone Partners | London | https://livingstonepartners.com/en-gb/careers |
| Lloyds Bank Corporate Markets | London | https://lloydsbankinggroup.com/careers |
| LocalGlobe (Latitude) | London | https://localglobe.vc |
| Lombard Odier | Geneva, London, Lugano, Milan | https://www.lombardodier.com/home/careers.html |
| Lombard Odier (Europe) S.A. | Luxembourg | https://www.lombardodier.com/home/careers.html |
| Lombard Odier Asset Management (Switzerland) SA | Geneva | https://www.lombardodier.com/home/careers/emerging-talent.html |
| Lombard Odier Middle East | Dubai | https://www.lombardodier.com/home/careers.html |
| Lumina Capital Advisers | Dubai | https://www.lumina-advisers.com/careers |
| M&G Investments | London | https://mandg.com/careers |
| M&G Luxembourg S.A. | Luxembourg | https://careers.mandg.com |
| MCP (Mandarin Capital Partners) | Milan | https://www.mcpinvest.com/contact |
| MOMentum Alternative Investments SA | Lugano | https://www.momentum.ch/ |
| Macquarie Business Banking | Sydney | https://www.macquarie.com/au/en/careers.html |
| Macquarie Group Limited | London, Sydney | https://macquarie.com/uk/en/careers.html |
| Maerki Baumann & Co AG | Lugano | https://www.maerki-baumann.ch/ |
| MainFirst Affiliated Fund Managers | Luxembourg | https://www.mainfirst.com/en/career |
| Majid Al Futtaim | Dubai | https://www.majidalfuttaim.com/en/careers |
| Man Group | London | https://man.com/careers |
| Mangrove Capital Partners | Luxembourg | https://www.mangrove.vc/contact |
| Marlborough Partners | London | https://marlboroughpartners.com/careers |
| Marshall Wace | Dubai | https://www.mwam.com/careers |
| Marshall Wace Asset Management Ltd | London | https://www.mwam.com/join-us/ |
| Mashreq Capital | Dubai | https://www.mashreq.com/en/uae/careers/ |
| Mayfair Equity Partners | London | https://mayfairequity.com |
| McKinsey | London | https://mckinsey.com/careers |
| McKinsey & Company | Dubai, Milan | https://www.mckinsey.com/it/careers |
| McKinsey + Company | Zurich | https://www.mckinsey.com/ch/careers |
| Mediobanca Banca Di Credito Finanziario Spa | Milan | https://www.mediobanca.com/it/lavora-con-noi/index.html |
| Mediobanca Management Company S.A. | Luxembourg | https://www.mediobanca.com/en/careers |
| Mediobanca Premier | Milan | https://www.mediobanca.com/it/lavora-con-noi |
| Mediolanum | Milan | https://www.bancamediolanum.it/lavora-con-noi |
| Middle East Venture Partners (MEVP) | Dubai | https://www.mevp.com/careers |
| Millennium Capital Partners | London | https://mlp.com/careers |
| Millennium Management | Dubai | https://www.mlp.com/careers |
| Mirabaud | Dubai, Geneva | https://www.mirabaud.com/en/careers |
| Moelis & Company | Dubai, London | https://moelis.com/careers |
| Molten Ventures | London | https://moltenventures.com/careers |
| Muzinich & Co. (Luxembourg) S.à r.l. | Luxembourg | https://www.muzinich.com/contact |
| Muzinich & Co. SGR | Milan | https://www.muzinich.com/careers |
| NB Renaissance (Neuberger Berman) | Milan | https://www.nb.com/en/global/careers |
| Nash Advisory | Milan | https://www.nashadvisory.com/carriere |
| NatWest Markets | London | https://jobs.natwestgroup.com |
| Naya Capital Management | Dubai | https://www.nayacapital.com |
| Nextalia Investment Management | Milan | https://nextalia.com/careers/ |
| Ninety One | London | https://ninetyone.com/en/careers |
| Nomura International plc | London | https://nomura.com/europe/careers |
| Nordea Investment Funds S.A. | Luxembourg | https://www.nordea.com/en/careers |
| Northern Trust Global Services SE | Luxembourg | https://careers.northerntrust.com |
| Novum Capital Partners | Dubai | https://www.novumcapitalpartners.com |
| Nuwa Capital | Dubai | https://www.nuwacapital.io |
| OC&C Strategy Consultants | London, Milan | https://www.occstrategy.com/en/careers |
| Octopus Ventures | London | https://octopusventures.com/careers |
| Oliver Wyman | Dubai, London, Milan | https://www.oliverwyman.com/careers.html |
| Ondra Partners | London | https://ondrapartners.com |
| One Fund Management S.A. (One Group) | Luxembourg | https://www.one-gs.com/careers |
| Oracle Capital Group | London | https://orcap.co.uk/careers |
| Oxy Capital | Milan | https://www.oxycapital.com/contacts |
| P101 SGR | Milan | https://www.p101.it/contact |
| PAI Partners | Milan | https://www.paipartners.com/contact |
| PAI Partners S.à r.l. | Luxembourg | https://www.paipartners.com/contact |
| PIMCO Italy | Milan | https://www.pimco.com/en-eu/careers |
| PJT Partners | Dubai, London | https://pjtpartners.com/careers |
| PKB Privatbank | Lugano | https://www.pkb.ch/it/carriera |
| Panakès Partners SGR | Milan | https://www.panakes.it/contacts |
| Panmure Liberum | London | https://panmureliberum.com/careers |
| Pantheon Ventures | London | https://pantheon.com/careers |
| Partners Group | Zug | https://jobs.partnersgroup.com/ |
| Partners Group (Luxembourg) S.A. | Luxembourg | https://www.partnersgroup.com/en/careers |
| Peel Hunt | London | https://peelhunt.com/careers |
| Pelham Capital | London | https://pelhamcapital.com |
| Pemberton Asset Management | London, Milan | https://pembertonam.com/careers |
| Perella Weinberg | London | https://pwpartners.com/careers |
| Perella Weinberg Partners (PWP) | Dubai | https://www.pwpartners.com/careers |
| Permira | London | https://permira.com/careers |
| Permira Advisers | Dubai | https://www.permira.com/careers |
| Petrus Advisers | Milan | https://petrusadvisers.com/careers |
| Pharus Management Lux S.A. | Luxembourg | https://www.pharusmanagement.com/lu/it/contatti |
| Phoenix Equity Partners | London | https://phoenix-equity.com |
| Pictet & Cie (Europe) + FundPartner Sol. | Luxembourg | https://www.pictet.com/ch/en/careers |
| Pictet & Cie Group SCA | Geneva | https://www.pictet.com/global/en/careers/graduate-programmes |
| Pictet Asset Management (Europe) S.A. | Luxembourg | https://www.pictet.com/ch/en/careers |
| Pictet Geneva | Geneva | https://www.pictet.com/global/en/careers/internship-programmes |
| Pictet Wealth Management | Milan | https://www.group.pictet/careers |
| Pictet Wealth Management ME | Dubai | https://www.group.pictet/careers |
| Pillarstone Italy | Milan | https://www.pillarstone.com/contact-us |
| Plenisfer Investments SGR | Milan | https://www.plenisfer.com/it/careers |
| Point72 | Dubai, Sydney | https://www.point72.com/careers |
| Point72 Europe | London | https://point72.com/careers |
| Polus Capital Management | London | https://poluscapital.com/careers |
| Prelios SGR | Milan | https://www.prelios.com/it/carriere |
| Primo Ventures SGR | Milan | https://www.primoventures.com/contacts |
| Privalux Management S.A. | Luxembourg | https://www.privalux.lu/en/contact |
| Pure Capital S.A. | Luxembourg | https://www.purecapital.eu/en/contact |
| PwC | Dubai, London, Melbourne, Milan, Perth, Sydney | https://www.pwc.com/it/it/careers.html |
| PwC Luxembourg | Luxembourg | https://www.pwc.lu/en/careers.html |
| Qbera Capital | Dubai | https://www.qberacapital.com |
| Quadrivio Group | Milan | https://www.quadriviogroup.com/it/careers |
| Quaestio Capital SGR | Milan | https://www.quaestiocapital.com/it/carriere |
| QuattroR SGR | Milan | https://www.quattror.com/contatti |
| Quilvest Wealth Management | Luxembourg | https://www.quilvestwealthmanagement.com/careers |
| Quintet Private Bank (Europe) S.A. | Luxembourg | https://www.quintet.com/en-lu/careers |
| RBC Capital Markets (UK) | London | https://jobs.rbc.com |
| RBS International Depositary Services | Luxembourg | https://jobs.natwestgroup.com |
| REYL Finance (MEA) | Dubai | https://www.reyl.com/en/careers |
| RIT Capital Partners | London | https://ritcap.com |
| RSM UK | London | https://rsmuk.com/careers |
| Rasmala Investment Bank | Dubai | https://www.rasmala.com/careers |
| Red Circle Investments | Milan | https://www.redcircleinvestments.it |
| Redalpine Venture Partners AG | Zug | https://redalpine.com/careers |
| Rede Partners | London | https://redepartners.com/careers |
| Reuben Brothers | London | https://reubenbrothers.com |
| Riello Investimenti SGR | Milan | https://www.rielloinvestimenti.it/contatti |
| Robeco Italy | Milan | https://www.robeco.com/en-int/careers |
| Robey Warshaw | London | https://robeywarshaw.com |
| Rokos Capital Management | London | https://rokoscapital.com/careers |
| Roland Berger | Milan | https://www.rolandberger.com/it/Join |
| Roland Berger Middle East | Dubai | https://www.rolandberger.com/en/Join/ |
| Rothschild & Co | London | https://www.rothschildandco.com/en/careers/students-and-graduates/opportunities/ |
| Rothschild & Co Bank | Milan | https://www.rothschildandco.com/en/careers |
| Rothschild & Co Middle East | Dubai | https://www.rothschildandco.com/en/careers |
| Route Capital Partners | Milan | https://www.routecapital.it/contatti |
| Ruffer LLP | London | https://ruffer.co.uk/about/careers |
| SHUAA Capital | Dubai | https://www.shuaa.com/careers |
| SMBC Bank International | London | https://smbcgroup.com/emea/careers |
| Sancta Capital | Dubai | https://www.sanctacapital.com |
| Sandaire (Schroders Family Office) | London | https://schroders.com/en/working-here |
| Santander CIB | Milan | https://www.santander.com/en/careers |
| Savills IM SGR | Milan | https://www.savillsim.com/careers |
| Schonfeld Strategic Advisors | Dubai | https://www.schonfeld.com/careers |
| Schroder Investment Management (Europe) | Luxembourg | https://www.schroders.com/en/careers |
| Schroders Investment Management | London | https://schroders.com/en/working-here |
| Schroders Italy SIM | Milan | https://www.schroders.com/en/global/individual/careers |
| Schroders Personal Wealth | London | https://spw.com/careers |
| Sculptor Capital Management | Dubai | https://www.sculptor.com/careers |
| Sedco Capital / Golden Gate | Dubai | https://www.sedco.com/careers |
| Seedcamp | London | https://seedcamp.com/jobs |
| Shorooq Partners | Dubai | https://www.shorooq.com/careers |
| Silchester International Investors | London | https://silchester.com |
| Silverpeak | London | https://silverpeakib.com/about-us/careers |
| Simon-Kucher | Milan | https://www.simon-kucher.com/en/careers |
| Soprarno SGR | Milan | https://www.soprarnosgr.it/contatti |
| Sovereign Capital Partners | London | https://sovereigncapital.co.uk/careers |
| Space Holding | Milan | https://www.spaceholding.it/contatti |
| Spayne Lindsay & Co. | London | https://spaynelindsay.com |
| Spencer House Partners | London | https://spencerhousepartners.com |
| Squarepoint Capital | Dubai | https://www.squarepoint-capital.com/careers |
| Stamford Partners | London | https://stamfordpartners.com |
| Standard Chartered | London | https://sc.com/en/careers |
| Stanhope Capital | London | https://stanhopecapital.com/contact |
| State Street Bank International (Lux) | Luxembourg | https://careers.statestreet.com |
| Stirling Haigh | Dubai | https://www.stirlinghaigh.com |
| Stonehage Fleming | Dubai, London, Luxembourg | https://stonehagefleming.com/careers |
| Strategy& Middle East | Dubai | https://www.strategyand.pwc.com/m1/en/careers.html |
| Swan Asset Management SA | Lugano | https://www.swan-am.com/ |
| Swicorp | Dubai | https://www.swicorp.com/careers |
| Swiss Life Asset Managers | Zurich | https://www.swisslife-am.com |
| SwissWealth Management SA (SWM) | Lugano | https://www.swisswealth.ch/ |
| Sycomore Asset Management | Milan | https://en.sycomore-am.com/careers |
| Sygnum Bank | Zurich | https://www.sygnum.com |
| Symphonia | Milan | https://www.symphonia.it/ |
| Synova | London | https://synova.pe |
| TCI Fund Management | London | https://tcifund.com |
| TDR Capital | London | https://tdrcapital.com/careers |
| TIP (Tamburi Investment Partners) | Milan | https://www.tipspa.it/contatti |
| TMF Luxembourg S.A. | Luxembourg | https://careers.tmf-group.com |
| TVM Capital Healthcare | Dubai | https://www.tvmcapitalhealthcare.com/careers |
| Tages Capital SGR | Milan | https://www.tagesgroup.com/contacts |
| Taurus Asset Management SA | Lugano | https://en.taurusfamily.ch/ |
| Teneo (Financial Advisory) | London | https://teneo.com/careers |
| The Family Office Co. (TFO) | Dubai | https://www.tfoco.com/en/careers |
| Tikehau Capital | Milan | https://www.tikehaucapital.com/en/careers |
| Torch Partners | London | https://torchpartners.com/careers |
| Tosetti Value SIM | Milan | https://www.tosettivalue.it/contatti |
| Triton Investment Management S.à r.l. | Luxembourg | https://www.triton-partners.com/careers |
| UBS | London, Lugano, Melbourne, Sydney | https://www.ubs.com/global/en/careers.html |
| UBS Europe SE | Milan | https://www.ubs.com/global/en/careers.html |
| UBS Europe SE, Luxembourg Branch | Luxembourg | https://www.ubs.com/global/en/careers.html |
| UBS-Geschäftsstelle | Zurich | https://www.ubs.com/global/en/careers.html |
| UI efa S.A. (European Fund Administration) | Luxembourg | https://www.efa.eu/en/careers |
| Ufenau Capital Partners | Pfaeffikon | https://www.ufenau.com |
| UniCredit | Milan | https://www.unicreditgroup.eu/en/careers.html |
| Unigestion | Geneva | https://www.unigestion.com |
| Union Bancaire Privée (UBP) ME | Dubai | https://www.ubp.com/en/careers |
| Union Bancaire Privée (UBP) SA | Geneva, Lugano | https://www.ubp.com/en/careers |
| United Ventures SGR | Milan | https://www.unitedventures.com/jobs |
| Universal-Investment-Luxembourg S.A. | Luxembourg | https://www.universal-investment.com/en/careers |
| VECO Group SA | Lugano | https://www.vecogroup.ch/en/ |
| ValeCap | Milan | https://www.valecap.com/contacts |
| Valeur SA (Valeur Group) | Lugano | https://www.valeur.ch/ |
| Valori Asset Management | Milan | https://www.valoriam.com/careers |
| ValuStrat | Dubai | https://www.valustrat.com/careers |
| Value Partners | Milan | https://www.valuepartners.com/carriere |
| Vanguard | London, Zurich | https://www.vanguardjobs.com/ |
| VentureSouq (VSQ) | Dubai | https://www.venturesouq.com |
| Ver Capital SGR | Milan | https://www.vercapital.com/contacts |
| Veritas Asset Management | London | https://vamllp.com |
| Verition | Dubai | https://www.verition.com/careers |
| Vistra (Luxembourg) S.à r.l. | Luxembourg | https://www.vistra.com/careers |
| Vitale & Co. | Milan | https://www.vitale-co.com/ |
| Vontobel | Lugano, Zurich | https://www.vontobel.com/en-ch/about-vontobel/careers/ |
| Wamda Capital | Dubai | https://www.wamdacapital.com |
| Waystone Management Company (Lux) S.A. | Luxembourg | https://www.waystone.com/careers |
| Weatherbys Private Bank | London | https://weatherbys.bank/careers |
| Wendel Luxembourg S.A. | Luxembourg | https://www.wendelgroup.com/en/careers |
| Winton Group | London | https://winton.com/careers |
| Wise Equity SGR | Milan | https://www.wisequity.com/contatti |
| Wren Investment Office | London | https://wreninvestmentoffice.com |
| Wrise Wealth Management ME | Dubai | https://www.wrise.com/careers |
| Xenon Private Equity | Milan | https://www.xenonpe.com/contacts |
| Zaoui & Co | London | https://zaouico.com |
| Zürcher Kantonalbank | Zurich | https://www.zkb.ch |
| illimity Bank | Milan | https://www.illimity.com/it/carriere |

</details>


### D. Additional companies awaiting your approval (12)

| Company | Category | City | Website | Reason |
|---|---|---|---|---|
| Bellevue Asset Management | Asset Manager | Zurich | https://www.bellevue.ch | Specialist asset manager (healthcare equities, private markets) in the Zurich area. Website entered from general knowledge and not yet fetched: confirm it when you review. |
| Capvis | PE | Zug | https://www.capvis.com | Swiss mid-market buy-out fund based in Baar (canton Zug). Website entered from general knowledge and not yet fetched: confirm it when you review. |
| Intesa Sanpaolo IMI Corporate & Investment Banking | Bulge Bracket | Milan | https://group.intesasanpaolo.com | Milan investment-banking arm of Intesa Sanpaolo; the Excel lists only group subsidiaries (career page taken from the Fideuram row). |
| Kepler Cheuvreux | Boutique IB | Milan | https://www.keplercheuvreux.com | European equity research, ECM and corporate-finance house with offices in Milan, Zurich and Geneva. Website entered from general knowledge and not yet fetched: confirm it when you review. |
| LGT Capital Partners | Asset Manager | Pfaeffikon | https://www.lgtcp.com | Alternative-investment manager (private equity, hedge funds) in Pfaeffikon SZ; the Excel only lists LGT Bank. Website entered from general knowledge and not yet fetched: confirm it when you review. |
| Leonteq | Altro | Zurich | https://www.leonteq.com | Zurich structured-products and derivatives house: relevant for quantitative and structuring roles. Website entered from general knowledge and not yet fetched: confirm it when you review. |
| Swiss Life Asset Managers | Asset Manager | Zurich | https://www.swisslife-am.com | Large Zurich asset manager (real assets, fixed income, equities). Website entered from general knowledge and not yet fetched: confirm it when you review. |
| Sygnum Bank | Banca privata | Zurich | https://www.sygnum.com | Zurich digital-asset bank with asset-management and research teams. Website entered from general knowledge and not yet fetched: confirm it when you review. |
| Ufenau Capital Partners | PE | Pfaeffikon | https://www.ufenau.com | Swiss private-equity firm (service-sector buy-and-build) in Pfaeffikon SZ, near Zurich and Zug. Website entered from general knowledge and not yet fetched: confirm it when you review. |
| UniCredit | Bulge Bracket | Milan | https://www.unicreditgroup.eu | Milan CIB and advisory franchise; the Excel lists only its subsidiary Cordusio SIM (career page taken from that Excel row). |
| Unigestion | Asset Manager | Geneva | https://www.unigestion.com | Geneva asset manager with private-equity and equities teams. Website entered from general knowledge and not yet fetched: confirm it when you review. |
| Zürcher Kantonalbank | Altro | Zurich | https://www.zkb.ch | Zurich cantonal bank with asset management (Swisscanto), research and corporate-finance units. Website entered from general knowledge and not yet fetched: confirm it when you review. |

### E. Sources that cannot be automated by design

- **LinkedIn**: not polled (terms of service). Search links per company and manual capture only.
- **jobs.ch, Jobup.ch, eFinancialCareers, Indeed, Karriere.ch, JobRoom**: no free public API; search links only.
- **Adzuna**: official API, optional; needs your free developer key (`ADZUNA_APP_ID`, `ADZUNA_APP_KEY`).
- **Taleo, iCIMS, Avature, tal.net, Umantis, Refline and similar**: detected and reported, no connector.
