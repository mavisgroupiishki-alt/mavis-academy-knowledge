/* Local media supplements for the trainee programme.
 * Existing leader edits, ordering and hidden tiles remain untouched. */
(()=>{
  const localVideo=(title,source)=>`<section class="trainee-sheet-source trainee-local-media"><h2>${title}</h2><video controls preload="metadata" playsinline src="media/${source}"></video></section>`;
  const localImage=(title,source)=>`<figure class="course-figure trainee-local-diagram"><img src="media/${source}" alt="${title}" loading="lazy"><figcaption class="course-figure-caption">${title}</figcaption></figure>`;
  const legacyDecisionMap=`<section class="trainee-sheet-source trainee-decision-map"><h2>Как определить маршрут по строительным работам</h2><p class="trainee-decision-map-lead">Идите по вопросам сверху вниз: так будет понятно, когда разрешительные документы не нужны, а когда проверяем СПК и аттестат.</p><ol class="trainee-decision-map-steps"><li><div><b>1. Что за работы?</b><span>Демонтаж, пусконаладочные работы или снос зданий и сооружений?</span></div><strong class="is-yes">Да → разрешительные документы не нужны</strong></li><li><div><b>2. Если нет — это текущий ремонт?</b><span>Например: поклейка обоев, штукатурка, замена полов по дефектному акту.</span></div><strong class="is-check">Да → уточняем состав работ и статус клиента</strong></li><li><div><b>3. Это крупные работы?</b><span>Новое строительство, реконструкция, модернизация или капитальный ремонт.</span></div><strong class="is-check">Да → определяем класс сложности объекта</strong></li><li><div><b>4. Какой класс сложности?</b><span>Для работ на объектах 1–4 класса дополнительно сверяем вид работ с перечнем, подлежащим аттестации.</span></div><strong class="is-route">1–4 класс + вид из перечня → СПК и аттестат</strong><strong class="is-route">5 класс или работа вне перечня → проверяем СПК</strong></li></ol></section>`;
  const generalRouteDiagram=localImage('Схема: как определить маршрут по строительным работам','day-1-general-info-route.png');
  const bitrixRegulation=String(window.MAVIS_BITRIX_REGULATION_HTML||'');
  const upsellTileContent=`<section class="trainee-sheet-source trainee-upsell-script">
    <h2>Допродажи: сценарии и выбор решения</h2>
    <p>Используйте этот сценарий после основной услуги, когда дополнительный продукт помогает клиенту закрыть понятную потребность.</p>

    <article class="source-block source-block--overview">
      <p class="source-block-label">СХЕМА ВЫБОРА</p>
      <h3 class="source-block-heading">Что предложить строительной компании</h3>
      <div class="trainee-upsell-map" role="list" aria-label="Выбор решения для допродажи">
        <article role="listitem"><b>Тендеры + госзаказчики</b><span>ISO 9001 + ISO 45001</span></article>
        <article role="listitem"><b>Тендеры без госзаказчиков</b><span>ISO 9001 + документы по охране труда</span></article>
        <article role="listitem"><b>Госзаказчики без тендеров</b><span>ISO 45001</span></article>
        <article role="listitem"><b>Нет тендеров и госзаказчиков</b><span>Документы по охране труда</span></article>
      </div>
    </article>

    <article class="source-block source-block--workflow">
      <p class="source-block-label">СЦЕНАРИЙ 01</p>
      <h3 class="source-block-heading">Тендерные сертификаты: ISO 9001 и ISO 45001</h3>
      <div class="source-block-body">
        <h4>Установление контакта</h4>
        <p class="trainee-upsell-quote">«Добрый день! Меня зовут Ирина, компания Mavis Group. Ранее работали с вами и получили все разрешающие документы на строительство. Хочу уточнить: участвуете ли вы в тендерах?»</p>
        <h4>Квалификация</h4>
        <ul>
          <li>Планируете участвовать только в белорусских тендерах или российские тоже рассматриваете?</li>
          <li>Работаете с госзаказчиками?</li>
          <li>Планируете участие в тендерах в ближайшее время?</li>
        </ul>
        <p>Если клиент пока не участвует: предложите рассмотреть сертификаты на будущее. По материалу плитки без ISO 9001 компания теряет до 60% тендеров. При работе с госзаказчиками нужен сертификат по охране труда.</p>
        <h4>Презентация решения</h4>
        <ul>
          <li><b>ГОСТ Р ИСО 9001-2015</b> — тендеры РФ и РБ.</li>
          <li><b>СТБ ISO 9001-2015</b> — тендеры РБ.</li>
          <li><b>Международный сертификат ISO 9001:2015</b> — большие сроки и высокая цена.</li>
        </ul>
        <p>«Мы подготовим весь пакет документов и решим вопросы по требованиям. От вас нужен один аттестованный совместитель и документы по охране труда — остальное берём на себя».</p>
        <h4>Варианты предложения</h4>
        <ul>
          <li><b>ISO 9001 + ISO 45001:</b> два сертификата, возможность участвовать в тендерах и работать с госзаказчиками; в исходном материале указана экономия 40% на пошлине при оформлении пакета.</li>
          <li><b>ISO 9001 + документы по охране труда:</b> для тендеров без госзаказчиков; закрывает вопрос с обязательными документами по охране труда.</li>
          <li><b>Документы по охране труда:</b> инструкции, наряды-допуски, риски и актуальные приказы; нужны для работы на строительном объекте.</li>
        </ul>
      </div>
    </article>

    <article class="source-block source-block--important">
      <p class="source-block-label">ОТРАБОТКА ВОЗРАЖЕНИЙ</p>
      <h3 class="source-block-heading">Сохранить сделку через минимальный продукт</h3>
      <div class="source-block-body trainee-upsell-objections">
        <article><b>«Зачем мне ISO 45001, если его редко требуют?»</b><p>Госзаказчики иногда запрашивают его: без сертификата не пройти квалификацию на тендер. Документы по охране труда всё равно придётся делать; при травме на объекте сертификат снижает риски перед проверяющими.</p></article>
        <article><b>«Дорого»</b><p>Сертификаты выдаются на три года. Один выигранный тендер может окупить их во много раз — это инвестиция, а не расход.</p></article>
        <article><b>«Сейчас не актуально»</b><p>Срочный объект может появиться, когда документов ещё нет. Очередь на аттестат — до пяти недель, а охрана труда актуальна всегда.</p></article>
      </div>
      <h4>Закрытие</h4>
      <p class="trainee-upsell-quote">«Давайте оформим сразу оба — это дешевле и надёжнее. Начнём с ISO 9001: он нужен в каждом втором тендере. ISO 45001 можно добавить позже, но в пакете выгоднее».</p>
      <p>По исходному сценарию сертификация занимает 5–7 рабочих дней, а получение полного пакета может занять около месяца — сроки всегда уточняйте перед обещанием клиенту.</p>
    </article>

    <article class="source-block source-block--workflow">
      <p class="source-block-label">СЦЕНАРИЙ 02</p>
      <h3 class="source-block-heading">Аттестат: повышение категории</h3>
      <div class="source-block-body">
        <h4>Войти в диалог через факт</h4>
        <p class="trainee-upsell-quote">«Подскажите, пожалуйста, у вас сейчас аттестат соответствия какой категории — 4-й?»</p>
        <p>Четвёртая категория ограничивает работу объектами самой низкой сложности.</p>
        <h4>Выявить потребность</h4>
        <p>«Планируете участвовать в тендерах на более крупные объекты или расширять виды работ?»</p>
        <h4>Показать выгоду</h4>
        <p>Переход на первую категорию даёт право работать на всех классах сложности — от 1 до 4. По материалу плитки с прошлого года аттестации подлежат дополнительные общестроительные, сантехнические, электротехнические и слаботочные виды работ.</p>
        <h4>Закрыть на следующий шаг</h4>
        <p class="trainee-upsell-quote">«Сейчас действует фиксированная цена. Давайте я отправлю список документов, которые нужно подготовить, а вы пришлёте реквизиты для договора. Удобнее на почту или в мессенджер?»</p>
      </div>
    </article>

    <article class="source-block source-block--reference">
      <p class="source-block-label">СЦЕНАРИЙ 03</p>
      <h3 class="source-block-heading">Реферальная программа</h3>
      <div class="source-block-body">
        <p>Предлагайте её особенно тогда, когда клиенту дорого и он хочет сэкономить.</p>
        <p class="trainee-upsell-quote">«У нас есть бонус: можно окупить наши услуги за счёт реферальной политики. Если у вас есть знакомые строительные, проектные или производственные компании, которым нужна сертификация, мы поможем. Вам будет 10% от их договора. Есть ли сейчас партнёры или знакомые, кого можно порекомендовать?»</p>
      </div>
    </article>
  </section>`;
  const bitrixTile={id:'tr-sheet-d2-bitrix24',icon:'▣',color:'aqua',title:'Работа с Bitrix24',eyebrow:'День 2 «Базовые скрипты и чек-листы»',lead:'',sources:[],attachments:[],content:`${localVideo('Видео: как правильно закрывать просроченные дела в CRM','bitrix-overdue-tasks.mp4')}<p><a class="trainee-resource-link" href="media/workflow-policy-overhaul.pdf" target="_blank" rel="noopener noreferrer">Открыть презентацию</a></p>${bitrixRegulation}`,assignment:null,importedSheet:false,curriculumTemplate:'trainee-sheets-2026-11-13.1',check:{q:'Видео и презентация по Bitrix24 изучены?',options:['Да, изучены','Нет, нужно вернуться к материалам'],answer:0,order:[]}};
  function appendOnce(course,marker,markup){if(course&&!String(course.content||'').includes(marker))course.content=`${course.content||''}${markup}`;}
  function apply(courses,days){
    if(!Array.isArray(courses)||!Array.isArray(days))return {courses,days};
    const byId=id=>courses.find(course=>course&&course.id===id);
    const general=byId('tr-sheet-d1-02');
    if(general&&String(general.content||'').includes(legacyDecisionMap))general.content=String(general.content).replace(legacyDecisionMap,generalRouteDiagram);
    appendOnce(byId('tr-sheet-d1-01'),'day-1-video-route.png',localImage('Схема: путь клиента в Mavis','day-1-video-route.png'));
    appendOnce(general,'mavis-group-overview.mp4',`${localVideo('Видео-обучение','mavis-group-overview.mp4')}${generalRouteDiagram}`);
    appendOnce(general,'day-1-general-info-route.png',generalRouteDiagram);
    appendOnce(byId('tr-sheet-d1-03'),'spk-10-days.mp4',localVideo('Видео: как получить свидетельство СПК за 10 дней','spk-10-days.mp4'));
    appendOnce(byId('tr-sheet-d1-03'),'day-1-spk-route.png',localImage('Схема: путь к свидетельству СПК','day-1-spk-route.png'));
    appendOnce(byId('tr-sheet-d1-04'),'attestation-3-weeks.mp4',localVideo('Видео: как пройти строительную аттестацию за 3 недели','attestation-3-weeks.mp4'));
    appendOnce(byId('tr-sheet-d1-04'),'day-1-attestation-route.png',localImage('Схема: получение аттестата соответствия','day-1-attestation-route.png'));
    appendOnce(byId('tr-sheet-d1-05'),'iso-fast-implementation.mp4',localVideo('Видео: как внедрить ISO быстро','iso-fast-implementation.mp4'));
    appendOnce(byId('tr-sheet-d1-05'),'day-1-iso9001-route.png',localImage('Схема: ISO 9001','day-1-iso9001-route.png'));
    appendOnce(byId('tr-sheet-d1-06'),'day-1-iso45001-route.png',localImage('Схема: ISO 45001 / СУОТ','day-1-iso45001-route.png'));
    const upsell=byId('tr-sheet-d2-03');
    if(upsell&&String(upsell.content||'').includes('Скрипт по тендерным сертификатам - СТРОИТЕЛЬСТВО'))upsell.content=upsellTileContent;
    if(!byId(bitrixTile.id)){courses.push({...bitrixTile});const dayTwo=days[1];if(dayTwo){dayTwo.courseIds=Array.isArray(dayTwo.courseIds)?dayTwo.courseIds:[];dayTwo.courseIds.push(bitrixTile.id);}}
    appendOnce(byId(bitrixTile.id),'Регламент работы менеджеров в Bitrix24',bitrixRegulation);
    return {courses,days};
  }
  window.MAVIS_TRAINEE_MEDIA={apply};
  if(window.MAVIS_TRAINEE_PROGRAM)apply(window.MAVIS_TRAINEE_PROGRAM.courses,window.MAVIS_TRAINEE_PROGRAM.days);
})();
