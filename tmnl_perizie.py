<div class="layout">
  <!-- Header con informazioni generali -->
  <div class="flex flex--justify-between flex--align-center mb-16">
    <span class="title">Perizie CTU</span>
    <span class="label">{{ data_aggiornamento }}</span>
  </div>

  <!-- Loop attraverso le perizie -->
  {% for perizia in perizie %}
  <div class="item mb-16">
    <div class="content">
      <!-- Intestazione perizia -->
      <div class="flex flex--justify-between flex--align-center mb-8">
        <span class="title title--small">{{ perizia.numero }}</span>
        <span class="label">{{ perizia.tribunale }}</span>
      </div>

      {% if perizia.giudice != '' or perizia.luogo_iop != '' %}
      <div class="flex flex--justify-between mb-8">
        {% if perizia.giudice != '' %}
        <span class="description">Giudice: {{ perizia.giudice }}</span>
        {% endif %}
        {% if perizia.luogo_iop != '' %}
        <span class="description">{{ perizia.luogo_iop }}</span>
        {% endif %}
      </div>
      {% endif %}

      <!-- Grid delle milestone -->
      <div class="grid grid--4 gap-8">
        
        <!-- GIURAMENTO -->
        <div class="flex flex--column flex--align-center p-8 rounded-4 
                    {% if perizia.giur_urg %}bg--gray-70{% else %}bg--gray-10{% endif %}">
          <span class="label mb-4">Giuramento</span>
          <span class="value value--large 
                       {% if perizia.giur_urg %}text--white{% endif %}">
            {{ perizia.giur }}
          </span>
          <span class="description {% if perizia.giur_urg %}text--white{% endif %}">
            {{ perizia.giur_data }}
          </span>
        </div>

        <!-- INIZIO OPERAZIONI -->
        <div class="flex flex--column flex--align-center p-8 rounded-4
                    {% if perizia.inizio_urg %}bg--gray-70{% else %}bg--gray-10{% endif %}">
          <span class="label mb-4">Inizio IOP</span>
          <span class="value value--large
                       {% if perizia.inizio_urg %}text--white{% endif %}">
            {{ perizia.inizio }}
          </span>
          <span class="description {% if perizia.inizio_urg %}text--white{% endif %}">
            {{ perizia.inizio_data }}
          </span>
        </div>

        <!-- BOZZA -->
        <div class="flex flex--column flex--align-center p-8 rounded-4
                    {% if perizia.bozza_urg %}bg--gray-70{% else %}bg--gray-10{% endif %}">
          <span class="label mb-4">Bozza</span>
          <span class="value value--large
                       {% if perizia.bozza_urg %}text--white{% endif %}">
            {{ perizia.bozza }}
          </span>
          <span class="description {% if perizia.bozza_urg %}text--white{% endif %}">
            {{ perizia.bozza_data }}
          </span>
        </div>

        <!-- DEPOSITO -->
        <div class="flex flex--column flex--align-center p-8 rounded-4
                    {% if perizia.dep_urg %}bg--gray-70{% else %}bg--gray-10{% endif %}">
          <span class="label mb-4">Deposito</span>
          <span class="value value--large
                       {% if perizia.dep_urg %}text--white{% endif %}">
            {{ perizia.dep }}
          </span>
          <span class="description {% if perizia.dep_urg %}text--white{% endif %}">
            {{ perizia.dep_data }}
          </span>
        </div>

      </div>
    </div>
  </div>

  {% if forloop.last == false %}
  <div class="divider my-16"></div>
  {% endif %}

  {% endfor %}

</div>

<!-- Title Bar opzionale -->
<div class="title_bar">
  <img class="image" src="https://usetrmnl.com/images/plugins/trmnl--render.svg" />
  <span class="title">Perizie CTU</span>
  <span class="instance">{{ num_perizie }} attive</span>
</div>
