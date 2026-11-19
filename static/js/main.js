
document.addEventListener('DOMContentLoaded', () => {
  initAnimations();
  initNavigation();
  initAlerts();
  initForms();
  initWarnOverlay();
  initPasswordToggle();
  initConfirmActions();
});

function initAnimations() {
  try {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    document.querySelectorAll('.card, .hero, .page-header').forEach(el => observer.observe(el));
  } catch (e) {
  }
}

function initNavigation() {
  const currentPath = window.location.pathname;
  const links = document.querySelectorAll('.nav-links a');
  links.forEach(link => {
    try {
      const linkPath = new URL(link.href, window.location.origin).pathname;
      if (linkPath === currentPath) {
        link.classList.add('active');
      }
    } catch (e) {
    }
  });
}

function initAlerts() {
  document.querySelectorAll('.alert').forEach(alert => {
    const timer = setTimeout(() => closeAlert(alert), 5000);

    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '×';
    closeBtn.className = 'alert-close';
    closeBtn.addEventListener('click', () => {
      clearTimeout(timer);
      closeAlert(alert);
    });
    alert.appendChild(closeBtn);
  });
}

function closeAlert(alert) {
  alert.style.opacity = '0';
  alert.style.transform = 'translateY(-20px)';
  setTimeout(() => alert.remove(), 300);
}

function initForms() {
  document.querySelectorAll('textarea').forEach(textarea => {
    const autoSize = () => {
      textarea.style.height = 'auto';
      textarea.style.height = textarea.scrollHeight + 'px';
    };
    textarea.addEventListener('input', autoSize);
    autoSize();
  });

  document.querySelectorAll('form').forEach(form => {
    let submitting = false;
    form.addEventListener('submit', (event) => {
      // IMPORTANTE: no deshabilitar aquí el botón pulsado. Un control
      // deshabilitado dentro del evento 'submit' se excluye del POST, por lo
      // que las acciones que se distinguen por el nombre del botón
      // (update_status, submit_plan, add_evidence, add_finding, submit_report,
      // accept, reject, delegador_update_severity, assign_user) no se
      // guardaban. Solo evitamos envíos duplicados con una bandera.
      if (submitting) {
        event.preventDefault();
        return;
      }
      submitting = true;
    });
  });

  const modeSel = document.querySelector('select[name="reporting_mode"]');
  const relSel = document.querySelector('select[name="relationship"]');
  const personalSection = document.getElementById('section-personal');

  const setRequired = (name, required) => {
    const el = document.querySelector(`[name="${name}"]`);
    if (el) el.required = !!required;
    try {
      const lbl = document.querySelector(`label[for="id_${name}"]`);
      if (lbl) lbl.classList.toggle('required-field', !!required);
    } catch (e) {}
  };

  const applyPersonalVisibility = (scroll = false) => {
    if (!modeSel || !personalSection) return;
    const mode = (modeSel.value || '').trim();
    const isAnon = mode === 'anonimo';
    const isWithData = mode === 'con_datos';
    personalSection.classList.toggle('is-hidden', !isWithData);

    ['name','email','phone','company_role'].forEach(n => setRequired(n, !!isWithData));
    const needMatricula = isWithData && relSel && relSel.value === 'Colaborador';
    setRequired('reporter_matricula', needMatricula);

    if (scroll) {
      const targetId = isAnon ? 'section-description' : (isWithData ? 'section-personal' : null);
      const target = targetId ? document.getElementById(targetId) : null;
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const initIncidentRequired = () => {
    ['incident_state','incident_branch','incident_date','incident_time','knows_actor','category','reporter_role','has_witnesses'].forEach(n => setRequired(n, true));
  };

  const actorSel = document.querySelector('[name="knows_actor"]');
  const actorBlock = document.getElementById('actor-block');
  const witnessSel = document.querySelector('[name="has_witnesses"]');
  const witnessBlock = document.getElementById('witnesses-block');

  const toggleBlock = (sel, block, yesValues = ['True','si','Sí','SI']) => {
    if (!sel || !block) return;
    const v = (sel.value || '').toString();
    const show = yesValues.includes(v);
    block.classList.toggle('is-hidden', !show);
  };

  if (modeSel) {
    applyPersonalVisibility(false);
    modeSel.addEventListener('change', () => applyPersonalVisibility(true));
  }
  if (relSel) {
    relSel.addEventListener('change', () => applyPersonalVisibility(false));
  }
  setRequired('relationship', true);
  setRequired('reporting_mode', true);
  initIncidentRequired();
  toggleBlock(actorSel, actorBlock);
  toggleBlock(witnessSel, witnessBlock);
  if (actorSel) actorSel.addEventListener('change', () => toggleBlock(actorSel, actorBlock));
  if (witnessSel) witnessSel.addEventListener('change', () => toggleBlock(witnessSel, witnessBlock));
}

function initWarnOverlay() {
  try {
    const overlay = document.getElementById('warnOverlay');
    const btnAccept = document.getElementById('btnAcceptWarn');
    const btnCancel = document.getElementById('btnCancelWarn');
    const sections = document.getElementById('formSections');
    if (!overlay || (!btnAccept && !btnCancel)) return;
  if (btnAccept) {
    btnAccept.addEventListener('click', () => {
      overlay.style.display = 'none';
      try {
        const modeSel = document.querySelector('select[name="reporting_mode"]');
        if (sections && modeSel && modeSel.value) {
          sections.classList.remove('is-hidden');
        }
      } catch (e) {}
    });
  }
    if (btnCancel) {
      btnCancel.addEventListener('click', () => {
        try {
          const homeUrl = overlay.getAttribute('data-home') || '/denuncias/';
          window.location.href = homeUrl;
        } catch (e) {
          window.location.href = '/denuncias/';
        }
      });
    }
  } catch (e) {
  }
}

function initPasswordToggle(){
  try {
    const toggle = document.querySelector('.password-group .password-toggle');
    const input = document.getElementById('id_password');
    if (!toggle || !input) return;
    toggle.addEventListener('click', () => {
      const isPwd = input.getAttribute('type') === 'password';
      input.setAttribute('type', isPwd ? 'text' : 'password');
    });
  } catch (e) {}
}

// Reemplaza los atributos inline onclick="return confirm(...)" / "return false"
// por listeners, para no depender de 'unsafe-inline' en la CSP.
function initConfirmActions(){
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', (event) => {
      const message = el.getAttribute('data-confirm') || '¿Confirmas esta acción?';
      if (!window.confirm(message)) {
        event.preventDefault();
        event.stopPropagation();
      }
    });
  });
  document.querySelectorAll('[data-noop]').forEach(el => {
    el.addEventListener('click', (event) => event.preventDefault());
  });
}
