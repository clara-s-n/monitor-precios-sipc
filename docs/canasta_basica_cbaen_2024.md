# Canasta Básica - CBAEN 2024

## Resumen

Definición de canasta básica basada en el **Informe CBAEN 2024 (Tabla 2)** del Instituto Nacional de Estadística (INE) de Uruguay.

La canasta contiene **62 productos** encontrados en los datos del SIPC (2023-2025).

---

## Productos Incluidos (por categoría)

### 🥩 Carnes (3 productos)
- ✅ Carne picada vacuna
- ✅ Aguja vacuna
- ✅ Pollo entero fresco con menudos
- ❌ Asado de tira (no aparece en productos_2025.csv)
- ❌ Carne para milanesa (no aparece en productos_2025.csv)

### 🐟 Pescados y huevos (2 productos)
- ✅ Pescado fresco
- ✅ Huevos colorados
- ❌ Enlatados al natural (no aparece en productos_2025.csv)
- ❌ Enlatados en aceite (no aparece en productos_2025.csv)

### 🍎 Frutas (17 productos)
- ✅ Naranja Navel, Naranja Valencia
- ✅ Mandarina Avana, Mandarina Común, Mandarina Ellendale, Mandarina Zazuma
- ✅ Pera Francesa, Pera Packams, Pera Williams
- ✅ Manzana Fuji, Manzana Granny Smith, Manzana Red Chieff, Manzana Red Deliciosa, Manzana Roja, Manzana Royal Gala
- ✅ Banana Brasil, Banana Ecuador
- ✅ Durazno Pavía, Durazno Rey del Monte
- ✅ Frutilla
- ✅ Limón

### 🥬 Verduras (14 productos)
- ✅ Zanahoria
- ✅ Lechuga Crespa, Lechuga Mantecosa
- ✅ Tomate Americano, Tomate Perita
- ✅ Cebolla Seca, Cebolla de Verdeo
- ✅ Zapallo Criollo, Zapallo Kabutiá, Zapallo Calabacín
- ✅ Morrón Amarillo, Morrón Rojo, Morrón Verde
- ✅ Zapallito Redondo, Zapallito Zuchini
- ❌ Ajos (no aparece en productos_2025.csv)

### 🥔 Tubérculos (4 productos)
- ✅ Papa Blanca, Papa Rosada
- ✅ Boniato Arapery, Boniato Morado

### 🌾 Cereales (7 productos)
- ✅ Harina trigo común 0000, Harina trigo común 000
- ✅ Arroz blanco
- ✅ Fideos secos al huevo, Fideos secos semolados
- ✅ Pan flauta
- ✅ Pan de molde lacteado (aproximación a Pan Porteño)
- ❌ Galleta de campaña chica (no aparece en productos_2025.csv)
- ❌ Pan rallado (no aparece en productos_2025.csv)

### 🫘 Leguminosas (2 productos)
- ✅ Arvejas, Arvejas en conserva
- ❌ Lentejas, lentejones (no aparece en productos_2025.csv)

### 🍬 Azúcares y dulces (3 productos)
- ✅ Azúcar blanco
- ✅ Dulce de leche
- ✅ Dulce de membrillo

### 🧈 Aceites y grasas (3 productos)
- ✅ Aceite de soja
- ✅ Aceite de girasol
- ✅ Manteca

### ☕ Otros (infusiones / varios) (5 productos)
- ✅ Sal fina yodada fluorada
- ✅ Yerba mate común
- ✅ Agua de mesa con gas, Agua de mesa sin gas

---

## Productos NO Encontrados en SIPC

Los siguientes productos de la CBAEN 2024 **no están disponibles** en los datos del SIPC:

1. **Asado de tira** (carnes)
2. **Carne para milanesa** (carnes)
3. **Pescado enlatado al natural** (pescados)
4. **Pescado enlatado en aceite** (pescados)
5. **Ajos** (verduras)
6. **Galleta de campaña chica** (cereales)
7. **Pan rallado** (cereales)
8. **Lentejas / lentejones** (leguminosas)

**Total de productos faltantes:** 8

---

## Aproximaciones Realizadas

Algunos productos de la CBAEN no tienen equivalencia exacta en el SIPC. Se usaron las siguientes aproximaciones:

- **Pan Porteño** → `Pan de molde lacteado` (producto más similar disponible)
- **Pollo en cortes / pechuga / supremas** → `Pollo entero fresco con menudos` (único producto de pollo disponible)

---

## Implementación en Código

La canasta básica está definida en:

```python
# src/metrics/simple_metrics.py
# src/metrics/calculate_metrics.py

CANASTA_BASICA = [
    # 62 productos específicos por nombre
    "Carne picada vacuna",
    "Aguja vacuna",
    # ... (ver archivos para lista completa)
]
```

El filtrado se realiza por **nombre exacto del producto** (campo `nombre` en `dim_producto`), no por categoría.

---

## Métricas Calculadas

Con esta canasta se calculan:

1. **Costo de canasta básica por supermercado** - Suma de precios de todos los productos de la canasta por establecimiento y mes
2. **Ranking de supermercados** - Ordenamiento de supermercados según costo total de canasta (menor a mayor)
3. **Variación temporal** - Cambio en el costo de la canasta entre períodos

**Archivo de salida:** `data_sipc/exports_dashboard/canasta_basica.parquet`

---

## Referencias

- **Fuente:** Informe CBAEN 2024 (Tabla 2) - Instituto Nacional de Estadística (INE)
- **Datos:** SIPC - Sistema de Información de Precios al Consumidor
- **Período:** 2023-2025
