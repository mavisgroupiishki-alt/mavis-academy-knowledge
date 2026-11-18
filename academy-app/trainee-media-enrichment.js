/* Local media supplements for the trainee programme.
 * Existing leader edits, ordering and hidden tiles remain untouched. */
(()=>{
  const localVideo=(title,source)=>`<section class="trainee-sheet-source trainee-local-media"><h2>${title}</h2><video controls preload="metadata" playsinline src="media/${source}"></video></section>`;
  const localImage=(title,source)=>`<figure class="course-figure trainee-local-diagram"><img src="media/${source}" alt="${title}" loading="lazy"><figcaption class="course-figure-caption">${title}</figcaption></figure>`;
  const legacyDecisionMap=`<section class="trainee-sheet-source trainee-decision-map"><h2>Как определить маршрут по строительным работам</h2><p class="trainee-decision-map-lead">Идите по вопросам сверху вниз: так будет понятно, когда разрешительные документы не нужны, а когда проверяем СПК и аттестат.</p><ol class="trainee-decision-map-steps"><li><div><b>1. Что за работы?</b><span>Демонтаж, пусконаладочные работы или снос зданий и сооружений?</span></div><strong class="is-yes">Да → разрешительные документы не нужны</strong></li><li><div><b>2. Если нет — это текущий ремонт?</b><span>Например: поклейка обоев, штукатурка, замена полов по дефектному акту.</span></div><strong class="is-check">Да → уточняем состав работ и статус клиента</strong></li><li><div><b>3. Это крупные работы?</b><span>Новое строительство, реконструкция, модернизация или капитальный ремонт.</span></div><strong class="is-check">Да → определяем класс сложности объекта</strong></li><li><div><b>4. Какой класс сложности?</b><span>Для работ на объектах 1–4 класса дополнительно сверяем вид работ с перечнем, подлежащим аттестации.</span></div><strong class="is-route">1–4 класс + вид из перечня → СПК и аттестат</strong><strong class="is-route">5 класс или работа вне перечня → проверяем СПК</strong></li></ol></section>`;
  const generalRouteDiagram=localImage('Схема: как определить маршрут по строительным работам','day-1-general-info-route.png');
  const bitrixRegulation=String(window.MAVIS_BITRIX_REGULATION_HTML||'');
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
    if(!byId(bitrixTile.id)){courses.push({...bitrixTile});const dayTwo=days[1];if(dayTwo){dayTwo.courseIds=Array.isArray(dayTwo.courseIds)?dayTwo.courseIds:[];dayTwo.courseIds.push(bitrixTile.id);}}
    appendOnce(byId(bitrixTile.id),'Регламент работы менеджеров в Bitrix24',bitrixRegulation);
    return {courses,days};
  }
  window.MAVIS_TRAINEE_MEDIA={apply};
  if(window.MAVIS_TRAINEE_PROGRAM)apply(window.MAVIS_TRAINEE_PROGRAM.courses,window.MAVIS_TRAINEE_PROGRAM.days);
})();
