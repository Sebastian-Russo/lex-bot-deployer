Single Intent - Medicare Enrollment

Utterances:

- Medicare Enrollment
- Enroll in Medicare

Enter into convo with bot: P1370

P1370: Muy bien, Medicare. Un momento. Esta usted inscrito en Medicare?
P1370English: Ok, Medicare. One moment. Are you enrolled in Medicare?

P1370a: Probemos otra vez. Medicare. Esta usted inscrito en Medicare?
P1370aEnglish: Let's try again. Medicare. Are you enrolled in Medicare?

No > Block A (secondary path) see later
Yes > continue, P1372 (main_flow)

```
Slots: Confirmation 1(Yes/No)
Session Attributes:

- flowPhase: main_flow/block_a
- enrollmentStatus: enrolled/not_enrolled
```

P1372: Quiere una nueva tarjeta de medicare?
P1372English: Do you want a new medicare card?

P1372a: Probemos otra vez. Quiere obtener una tarjeta de reemplazo de medicare?
P1372aEnglish: Let's try again. Do you want a replacement medicare card?

Yes > Transfer to Medicare Replacement Card bot
No > continue, P1373

```
Slots: Confirmation 2(Yes/No)
Session Attributes:

- flowPhase: main_flow/end_flow (cuz transfer)
- wantReplacementCard: true/false
```

P1373: Esta llamando para solicitar ayuda para cubrir los gastos por medicamentos?
P1373English: Are you calling to get help covering the cost of medications?

P1373a: Probemos otra vez. Esta llamando para solicitar ayuda para cubrir los gastos por medicamentos?
P1373aEnglish: Let's try again. Are you calling to get help covering the cost of medications?

No > P1382 (return to main menu)
Yes > P1374 (main path)

```
Slots: Confirmation 3(Yes/No)
Session Attributes:

- flowPhase: main_flow/end_flow
- wantMedicationCostHelp: true/false
```

P1374: Ya esta usted inscrito en el programa de ayuda para cubrir gastos de medicamentos llamado parte D?
P1374English: Are you already enrolled in the program to help cover the cost of medications called Part D?

P1374a: Probemos otra vez. Ya esta usted inscrito en el programa de ayuda para cubrir gastos de medicamentos llamado parte D?
P1374aEnglish: Let's try again. Are you already enrolled in the program to help cover the cost of medications called Part D?

No > Block B (secondary path) see later below
Yes > continue, P1375 + P1376

```
Slots: Confirmation 4(Yes/No)
Session Attributes:

- flowPhase: main_flow/block_b
- alreadyEnrolledInMedicationCostHelp_PartD: true/false
```

P1375: Algunas personas pueden tener derecho a recibir ayuda para cubrir sus gastos por medicamentos. Para poder recibir la ayuda adicional, sus recursos deben sere menos de {$External.IndividualMaximum} para una persona, o de {$External.CoupleMaximum} para una matrimonio que vivan juntos. Ejemplos de Los recursos incluyen, sus ahorros, inversiones, y bienes inmuebles. No incluimos la casa en la que vive, los vehiculos, los terrenos funerarios, ni los objects personales. Sin embargo, hay limites de ingresos que se tomaran en cuenta si decide solicitar esta ayuda. Los cambios en la ley facilitaran que algunas personas tengan derecho a recibir ayuda adicional. El Seguro Social no tomara como ingreso la ayuda que reciba con los gastos del hogar, ni polizas de seguro de vida, para determinar su elegibilidad. Tambien puede obtener ayuda con los gastos de Medicare en su estado con el programa de ahorros de Medicare. Las solicitudes para esta ayuda pueden iniciar el proceso de solicitud para los programas de ahorro de Medicare en su estado. Enviaremos su informacion a su estado y ellos se pondran en comunicacion con usted para ayudarlo a solicitar los programas de ahorro de Medicare, a menos que nos diga que no lo hagamos.
P1375English: Some people may have the right to receive help covering their medication expenses. To receive additional help, your resources must be less than {$External.IndividualMaximum} for an individual, or {$External.CoupleMaximum} for a married couple living together. Examples of resources include savings, investments, and real estate. We do not include the house you live in, vehicles, burial plots, or personal property. However, there are income limits that will be taken into account if you decide to apply for this help. The law changes will allow some people to have the right to receive additional help. The Social Security Administration will not consider the help you receive for home expenses or life insurance policies when determining your eligibility. You can also receive help with Medicare expenses in your state through the Medicare Savings Program. Applications for this help can begin the process of applying for Medicare Savings Programs in your state. We will send your information to your state and they will contact you to help you apply for Medicare Savings Programs, unless you tell us not to.

-

P1376: Quiere volver a escuchar la informacion otra vez?
P1376English: Do you want to hear the information again?

P1376a: Probemos otra vez. Quiere volver a escuchar la informacion sobre la ayuda para cubrir sus gastos por medicamentos?
P1376aEnglish: Let's try again. Do you want to hear the information about the help covering your medication expenses?

Yes > repeat P1375 + P1376
No > P1377 (main path)

```
Slots: Confirmation 5?(Yes/No)
Session Attributes:

- flowPhase: main_flow/repeat_p1375_p1376
- wantMedicationCostHelp_repeat: true/false
```

P1377: Desea usted recibir una applicacion para ayuda para cubrir sus gastos por medicamentos?
P1377English: Do you want to receive an application for help covering your medication expenses?

P1377a: Probemos otra vez. Desea usted recibir una applicacion para ayuda para cubrir sus gastos por medicamentos?
P1377aEnglish: Let's try again. Do you want to receive an application for help covering your medication expenses?

Yes > _Medicare Perscription Drug Extra Help_ (TODO: is this bot or link? Find out what it is.)
No > P1382 (return to main menu)

```
Slots: Confirmation 6 (Yes/No)
Session Attributes:

- flowPhase: end_flow
- wantToReceiveApplication: true/false
```

P1382: Si termino, puede desconectar. Si no, espere y lo regresare al menu principal.
P1382English: If you are finished, you can disconnect. If not, please wait and I will return you to the main menu.

```
No slot
Session Attributes:

- flowPhase: end_flow
```

Block B

P1380: Para inscribirse en el programa regular de Medicare de ayuda para cubrir gastos por medicamentos, llamado parte D, debe estar inscrito, o ser elegible a la Parte A de Medicare, de cobertura hospitalaria, o la Parte B, que ofrece servicios medicos, cobertura de vista medica y otros servicios no cubiertos por la Parte A. Una vez este inscrito en la Parte A, o la Parte B, puede inscribirse USTED MISMO en el programa de ayuda para cubrir gastos por medicamentos, llamado parte D, a treaves de un proveedor autorizado del programa para ayuda para cubrir gastos por medicamentos de Medicare, o a traves de un plan para cubrir gastos por medicamentos de Medicare que ofrece cobertura para cubrir gastos por medicamentos. Para obtener mas informacion, llame al 1-800-633-4227. Repitiendo el numero es, 1-800-633-4227, o visite el sitio web, Medicare punto G O V.
P1380English: To enroll in the regular Medicare program for help covering medication expenses, called Part D, you must be enrolled, or eligible for Part A of Medicare, hospital coverage, or Part B, which offers medical services, medical vision coverage, and other services not covered by Part A. Once you are enrolled in Part A or Part B, you can enroll yourself in the program for help covering medication expenses, called Part D, through an authorized provider of the program for help covering medication expenses of Medicare, or through a Medicare coverage plan for medication expenses that offers coverage for medication expenses. To get more information, call 1-800-633-4227. Repeating the number is, 1-800-633-4227, or visit the website, Medicare dot G O V.

-

P1381: Quiere volver a escuchar la informacion otra vez?
P1381English: Do you want to hear the information again?

P1381a: Probemos otra vez. Desea escuchar de nuevo la informacion para inscribirse en el programa regular de Medicare de ayuda para cubrir gastos por medicamentos?
P1381aEnglish: Let's try again. Do you want to hear the information about enrolling in the regular Medicare program for help covering medication expenses?
P1381aEnglish: Let's try again. Do you want to hear the information about enrolling in the regular Medicare program for help covering medication expenses?

Yes > repeat P1380 + P1381
No > P1382 (return to main menu)

```
Slots: Confirmation (Yes/No)
Session Attributes:

- flowPhase: main_flow/block_b
- wantsToHearAboutEnrollingInPartD: true/false

```

Block A

P1378: Usted puede obtener mas informacion sobre la ayuda para cubrir sus gastos por medicaments (conocido como Parte D) o los programas de Medicare estatales que pueden ayudarlo con sus gastos de salud, llamando a 1-800-633-4227. Ese numer es, 1-800-633-4227. Este informacion tambien esta disponible en su sitio web, en www punto Medicare punto G O V.
P1378English: You can get more information about the help covering your medication expenses (known as Part D) or the Medicare state programs that can help you with your health care expenses, by calling 1-800-633-4227. That number is, 1-800-633-4227. This information is also available on your website, at www dot Medicare dot G O V.

-

P1379: Quiere volver a escuchar la informacion otra vez?
P1379English: Do you want to hear the information again?

P1379a: Probemos otra vez. Desea escuchar la informacion para applicar a la parte D de Medicare nuevamente?
P1379aEnglish: Let's try again. Do you want to hear the information about applying fofr Part D of Medicare again?

Yes > repeat P1378 + P1379
No > P1382 (return to main menu)

```
Slots: Confirmation (Yes/No)
Session Attributes:

- flowPhase: main_flow/block_a
- wantsToHearAboutApplyingForPartD: true/false

```
