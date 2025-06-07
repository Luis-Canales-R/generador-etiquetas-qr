document.addEventListener('DOMContentLoaded', () => {
    // --- Referencias a Elementos del DOM ---
    const productListElement = document.getElementById('product-list');
    const labelPreviewElement = document.getElementById('label-preview');
    const sizeSelector = document.getElementById('size-selector');
    const printButton = document.getElementById('print-button');
    const addForm = document.getElementById('add-product-form');
    const productNameInput = document.getElementById('product-name');
    const inventoryNumberInput = document.getElementById('inventory-number');

    // --- Funciones Principales ---

    // Muestra la vista previa de la etiqueta
    function showQrCode(product) {
        labelPreviewElement.innerHTML = ''; 
        const productName = document.createElement('h3');
        productName.textContent = product.product_name;
        const inventoryId = document.createElement('p');
        inventoryId.textContent = `ID: ${product.inventory_number}`;
        const qrImage = document.createElement('img');
        qrImage.src = `/api/qr/${product.inventory_number}`; 
        labelPreviewElement.appendChild(productName);
        labelPreviewElement.appendChild(inventoryId);
        labelPreviewElement.appendChild(qrImage);
        printButton.disabled = false;
    }

    // Refresca la lista de productos desde la API
    function fetchAndRenderProducts() {
        fetch('/api/products')
            .then(response => response.json())
            .then(products => {
                productListElement.innerHTML = ''; // Limpiamos la lista actual
                products.forEach(product => {
                    const listItem = document.createElement('li');
                    
                    const nameSpan = document.createElement('span');
                    nameSpan.textContent = product.product_name;
                    listItem.appendChild(nameSpan);

                    const deleteBtn = document.createElement('button');
                    deleteBtn.textContent = 'Eliminar';
                    deleteBtn.className = 'delete-btn';
                    
                    // Evento para eliminar el producto
                    deleteBtn.addEventListener('click', (event) => {
                        event.stopPropagation(); // Evita que se dispare el clic de la lista
                        if (confirm(`¿Estás seguro de que quieres eliminar "${product.product_name}"?`)) {
                            fetch(`/api/products/${product.inventory_number}`, { method: 'DELETE' })
                                .then(() => fetchAndRenderProducts()); // Refresca la lista
                        }
                    });
                    
                    listItem.appendChild(deleteBtn);
                    
                    // Evento para mostrar la vista previa
                    listItem.addEventListener('click', () => showQrCode(product));
                    
                    productListElement.appendChild(listItem);
                });
            })
            .catch(error => console.error('Error al cargar los productos:', error));
    }

    // --- Event Listeners ---

    // Para el formulario de añadir producto
    addForm.addEventListener('submit', (event) => {
        event.preventDefault(); // Previene la recarga de la página
        const newProduct = {
            product_name: productNameInput.value,
            inventory_number: inventoryNumberInput.value
        };
        
        fetch('/api/products', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newProduct)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                addForm.reset(); // Limpia el formulario
                fetchAndRenderProducts(); // Refresca la lista
            } else {
                alert(`Error: ${data.message}`);
            }
        });
    });

    // Para el botón de imprimir
    printButton.addEventListener('click', () => {
        const selectedSizeClass = sizeSelector.value;
        labelPreviewElement.className = ''; // Limpia clases anteriores
        labelPreviewElement.classList.add(selectedSizeClass);
        window.print();
    });

    // --- Carga Inicial ---
    fetchAndRenderProducts();
});