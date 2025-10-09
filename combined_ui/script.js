const sidebarItems = document.querySelectorAll('.sidebar__item');
const panels = document.querySelectorAll('.panel');
const dealItems = document.querySelectorAll('.deal-list__item');
const dealDetailsTitle = document.querySelector('.deal-details__title');
const dealDetailsSubtitle = document.querySelector('.deal-details__subtitle');
const dealTimeline = document.querySelector('.timeline');

const dealData = {
  1: {
    title: 'ООО «Новые решения»',
    subtitle: 'CRM система • 820 000 ₽',
    timeline: [
      { date: '2025-10-08', label: '8 октября', text: 'Получен запрос на доработку интеграции с ERP.' },
      { date: '2025-10-05', label: '5 октября', text: 'Отправлено коммерческое предложение.' },
      { date: '2025-09-29', label: '29 сентября', text: 'Проведена демонстрация продукта.' }
    ]
  },
  2: {
    title: 'ИП Петров',
    subtitle: 'Мобильное приложение • 1 100 000 ₽',
    timeline: [
      { date: '2025-10-07', label: '7 октября', text: 'Согласован прототип приложения.' },
      { date: '2025-10-03', label: '3 октября', text: 'Получен отзыв по пользовательским сценариям.' }
    ]
  },
  3: {
    title: 'АО «ТехноСфера»',
    subtitle: 'Внедрение BI • 1 530 000 ₽',
    timeline: [
      { date: '2025-10-06', label: '6 октября', text: 'Подготовлены дашборды для пилота.' },
      { date: '2025-10-01', label: '1 октября', text: 'Утвержден бюджет проекта.' },
      { date: '2025-09-20', label: '20 сентября', text: 'Запущен аудит источников данных.' }
    ]
  }
};

sidebarItems.forEach((item) => {
  item.addEventListener('click', () => {
    const target = item.dataset.target;

    sidebarItems.forEach((btn) => btn.classList.toggle('sidebar__item--active', btn === item));
    panels.forEach((panel) => panel.classList.toggle('panel--active', panel.id === target));
  });
});

dealItems.forEach((item) => {
  item.addEventListener('click', () => {
    const id = item.dataset.dealId;
    const data = dealData[id];
    if (!data) return;

    dealItems.forEach((deal) => deal.classList.toggle('deal-list__item--active', deal === item));
    dealDetailsTitle.textContent = data.title;
    dealDetailsSubtitle.textContent = data.subtitle;

    dealTimeline.innerHTML = data.timeline
      .map(
        (entry) => `
          <li>
            <time datetime="${entry.date}">${entry.label}</time>
            <p>${entry.text}</p>
          </li>
        `.trim()
      )
      .join('');
  });
});
