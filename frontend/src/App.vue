<!-- frontend/src/App.vue -->
<template>
  <div class="app">
    <header class="app-header">
      <h1>Intuitive Care – Dashboard de Operadoras</h1>
      <p>Dados consumidos da API em Python (FastAPI).</p>
    </header>

    <section class="filtros">
      <div class="campo">
        <label for="busca">Buscar por Razão Social ou CNPJ:</label>
        <input
          id="busca"
          v-model="busca"
          type="text"
          placeholder="Ex.: UNIMED, 123..."
          @keyup.enter="carregarOperadoras(1)"
        />
      </div>

      <div class="campo">
        <label for="limit">Itens por página:</label>
        <select id="limit" v-model.number="limit" @change="carregarOperadoras(1)">
          <option :value="5">5</option>
          <option :value="10">10</option>
          <option :value="20">20</option>
        </select>
      </div>

      <button @click="carregarOperadoras(1)" :disabled="loading">
        {{ loading ? "Carregando..." : "Aplicar filtros" }}
      </button>
    </section>

    <section class="tabela">
      <h2>Operadoras</h2>

      <p v-if="erro" class="erro">{{ erro }}</p>

      <table v-if="operadoras.length > 0">
        <thead>
          <tr>
            <th>CNPJ</th>
            <th>Razão Social</th>
            <th>Modalidade</th>
            <th>UF</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="op in operadoras" :key="op.cnpj">
            <td>{{ op.cnpj }}</td>
            <td>{{ op.razao_social }}</td>
            <td>{{ op.modalidade || "-" }}</td>
            <td>{{ op.uf || "-" }}</td>
            <td>
              <button @click="selecionarOperadora(op)">Ver detalhes</button>
            </td>
          </tr>
        </tbody>
      </table>

      <p v-else-if="!loading">Nenhuma operadora encontrada.</p>

      <div class="paginacao" v-if="total > 0">
        <button @click="mudarPagina(page - 1)" :disabled="page <= 1">
          Anterior
        </button>
        <span>Página {{ page }} / {{ totalPages }}</span>
        <button @click="mudarPagina(page + 1)" :disabled="page >= totalPages">
          Próxima
        </button>
      </div>
    </section>

    <section class="detalhes" v-if="operadoraSelecionada">
      <h2>Detalhes da Operadora</h2>
      <p><strong>CNPJ:</strong> {{ detalhes?.cnpj }}</p>
      <p><strong>Razão Social:</strong> {{ detalhes?.razao_social }}</p>
      <p><strong>Modalidade:</strong> {{ detalhes?.modalidade || "-" }}</p>
      <p><strong>UF:</strong> {{ detalhes?.uf || "-" }}</p>
      <p>
        <strong>Total de Despesas:</strong>
        {{ detalhes?.total_despesas?.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }}
      </p>

      <h3>Histórico de Despesas (por trimestre)</h3>
      <p v-if="historico.length === 0 && !loadingHistorico">Sem dados de histórico.</p>

      <table v-if="historico.length > 0">
        <thead>
          <tr>
            <th>Ano</th>
            <th>Trimestre</th>
            <th>Despesas</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in historico" :key="item.ano + '-' + item.trimestre">
            <td>{{ item.ano }}</td>
            <td>{{ item.trimestre }}</td>
            <td>
              {{ item.valor_despesas.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) }}
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="grafico">
      <h2>Distribuição de Despesas – Top 5 Operadoras</h2>
      <canvas ref="chartCanvas"></canvas>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import Chart from "chart.js/auto";

const API_BASE = "http://localhost:8000";

const operadoras = ref([]);
const page = ref(1);
const limit = ref(10);
const total = ref(0);
const busca = ref("");

const loading = ref(false);
const erro = ref("");

const operadoraSelecionada = ref(null);
const detalhes = ref(null);
const historico = ref([]);
const loadingHistorico = ref(false);

const chartCanvas = ref(null);
let chartInstance = null;

const totalPages = computed(() =>
  total.value > 0 ? Math.ceil(total.value / limit.value) : 1
);

async function carregarOperadoras(pagina = 1) {
  loading.value = true;
  erro.value = "";
  try {
    const params = new URLSearchParams({
      page: String(pagina),
      limit: String(limit.value),
    });
    if (busca.value.trim() !== "") {
      params.append("busca", busca.value.trim());
    }

    const resp = await fetch(`${API_BASE}/api/operadoras?${params.toString()}`);
    if (!resp.ok) {
      throw new Error(`Erro ao buscar operadoras: ${resp.status}`);
    }
    const json = await resp.json();
    operadoras.value = json.data;
    page.value = json.page;
    limit.value = json.limit;
    total.value = json.total;
  } catch (e) {
    erro.value = e.message;
  } finally {
    loading.value = false;
  }
}

async function selecionarOperadora(op) {
  operadoraSelecionada.value = op;
  await carregarDetalhes(op.cnpj);
  await carregarHistorico(op.cnpj);
}

async function carregarDetalhes(cnpj) {
  try {
    const resp = await fetch(`${API_BASE}/api/operadoras/${encodeURIComponent(cnpj)}`);
    if (!resp.ok) throw new Error("Erro ao carregar detalhes");
    detalhes.value = await resp.json();
  } catch (e) {
    console.error(e);
  }
}

async function carregarHistorico(cnpj) {
  loadingHistorico.value = true;
  try {
    const resp = await fetch(`${API_BASE}/api/operadoras/${encodeURIComponent(cnpj)}/despesas`);
    if (!resp.ok) throw new Error("Erro ao carregar histórico");
    historico.value = await resp.json();
  } catch (e) {
    console.error(e);
    historico.value = [];
  } finally {
    loadingHistorico.value = false;
  }
}

async function carregarEstatisticas() {
  try {
    const resp = await fetch(`${API_BASE}/api/estatisticas`);
    if (!resp.ok) throw new Error("Erro ao carregar estatísticas");
    const json = await resp.json();

    const labels = json.top5_operadoras.map(
      (op) => `${op.razao_social} (${op.uf})`
    );
    const valores = json.top5_operadoras.map((op) => op.total_despesas);

    desenharGrafico(labels, valores);
  } catch (e) {
    console.error(e);
  }
}

function desenharGrafico(labels, valores) {
  if (!chartCanvas.value) return;

  if (chartInstance) {
    chartInstance.destroy();
  }

  chartInstance = new Chart(chartCanvas.value.getContext("2d"), {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Total de Despesas",
          data: valores,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: true },
      },
    },
  });
}

function mudarPagina(novaPagina) {
  if (novaPagina < 1 || novaPagina > totalPages.value) return;
  carregarOperadoras(novaPagina);
}

onMounted(() => {
  carregarOperadoras(1);
  carregarEstatisticas();
});
</script>

<style scoped>
.app {
  max-width: 1100px;
  margin: 0 auto;
  padding: 1.5rem;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.app-header {
  margin-bottom: 1.5rem;
}

.app-header h1 {
  margin: 0 0 0.5rem 0;
}

.filtros {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
  margin-bottom: 1.5rem;
}

.campo {
  display: flex;
  flex-direction: column;
}

.campo input,
.campo select {
  padding: 0.4rem 0.6rem;
  border-radius: 4px;
  border: 1px solid #ccc;
}

button {
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  border: none;
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.tabela table,
.detalhes table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 0.5rem;
}

table th,
table td {
  border: 1px solid #ddd;
  padding: 0.4rem 0.6rem;
  font-size: 0.9rem;
}

table th {
  background: #f5f5f5;
}

.paginacao {
  margin-top: 0.8rem;
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.erro {
  color: #b00020;
}

.grafico {
  margin-top: 2rem;
}
</style>
