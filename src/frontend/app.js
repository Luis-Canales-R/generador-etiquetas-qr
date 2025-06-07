document.addEventListener('DOMContentLoaded', () => {
    // Referencias a todos los elementos del DOM
    const productListElement = document.getElementById('product-list');
    const labelPreviewElement = document.getElementById('label-preview');
    const sizeSelector = document.getElementById('size-selector');
    const printButton = document.getElementById('print-button');
    const addForm = document.getElementById('add-product-form');
    const productNameInput = document.getElementById('product-name');
    const inventoryNumberInput = document.getElementById('inventory-number');
    const serialNumberInput = document.getElementById('serial-number');
    const brandInput = document.getElementById('brand');
    const modelInput = document.getElementById('model');
    const equipmentTypeInput = document.getElementById('equipment-type');
    const searchInput = document.getElementById('search-input');

    // Función para mostrar la vista previa de la etiqueta
    function showQrCode(product) {
        labelPreviewElement.innerHTML = '';
        
        const labelContent = document.createElement('div');
        labelContent.className = 'label-content';

        const textColumn = document.createElement('div');
        textColumn.className = 'text-column';

        const header = document.createElement('div');
        header.className = 'label-header';
        const logo = document.createElement('img');
        logo.src = '/assets/logo.png';
        logo.className = 'label-logo';
        
        // El span con el nombre de la empresa ha sido eliminado de aquí
        header.appendChild(logo);

        const inventoryId = document.createElement('p');
        inventoryId.className = 'inventory-id-text';
        inventoryId.textContent = product.inventory_number;

        const productName = document.createElement('p');
        productName.className = 'product-details-text';
        productName.textContent = product.product_name;

        const brand = document.createElement('p');
        brand.className = 'product-details-text';
        brand.textContent = product.brand;
        
        textColumn.appendChild(header);
        textColumn.appendChild(inventoryId);
        textColumn.appendChild(productName);
        textColumn.appendChild(brand);

        const qrColumn = document.createElement('div');
        qrColumn.className = 'qr-column';
        const qrImage = document.createElement('img');
        qrImage.src = `/api/qr/${product.inventory_number}`;
        qrColumn.appendChild(qrImage);

        labelContent.appendChild(textColumn);
        labelContent.appendChild(qrColumn);
        
        labelPreviewElement.appendChild(labelContent);

        printButton.disabled = false;
    }

    // Función para cargar y mostrar la lista de productos
    function fetchAndRenderProducts() {
        fetch('/api/products')
            .then(response => response.json())
            .then(products => {
                productListElement.innerHTML = '';
                products.forEach(product => {
                    const listItem = document.createElement('li');
                    const productInfoDiv = document.createElement('div');
                    productInfoDiv.className = 'product-info';
                    const nameSpan = document.createElement('span');
                    nameSpan.className = 'product-name';
                    nameSpan.textContent = product.product_name;
                    const detailsSpan = document.createElement('span');
                    detailsSpan.className = 'product-details';
                    detailsSpan.textContent = `ID: ${product.inventory_number} | Modelo: ${product.model} | Marca: ${product.brand}`;
                    productInfoDiv.appendChild(nameSpan);
                    productInfoDiv.appendChild(detailsSpan);
                    listItem.appendChild(productInfoDiv);
                    const deleteBtn = document.createElement('button');
                    deleteBtn.textContent = 'Eliminar';
                    deleteBtn.className = 'delete-btn';
                    deleteBtn.addEventListener('click', (event) => {
                        event.stopPropagation();
                        if (confirm(`¿Estás seguro de que quieres eliminar "${product.product_name}"?`)) {
                            fetch(`/api/products/${product.inventory_number}`, { method: 'DELETE' })
                                .then(() => fetchAndRenderProducts());
                        }
                    });
                    listItem.appendChild(deleteBtn);
                    listItem.addEventListener('click', () => showQrCode(product));
                    productListElement.appendChild(listItem);
                });
            })
            .catch(error => console.error('Error al cargar los productos:', error));
    }

    // --- Event Listeners ---
    searchInput.addEventListener('input', () => {
        const searchTerm = searchInput.value.toLowerCase();
        const productItems = productListElement.querySelectorAll('li');
        productItems.forEach(item => {
            const itemText = item.textContent.toLowerCase();
            if (itemText.includes(searchTerm)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    });

    addForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const newProduct = {
            product_name: productNameInput.value,
            inventory_number: inventoryNumberInput.value,
            serial_number: serialNumberInput.value,
            brand: brandInput.value,
            model: modelInput.value,
            equipment_type: equipmentTypeInput.value
        };
        fetch('/api/products', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newProduct)
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                addForm.reset();
                fetchAndRenderProducts();
            } else {
                alert(`Error: ${data.message}`);
            }
        });
    });

    printButton.addEventListener('click', () => {
        const selectedSizeClass = sizeSelector.value;
        labelPreviewElement.className = '';
        labelPreviewElement.classList.add(selectedSizeClass);
        window.print();
    });

    // --- Carga Inicial ---
    fetchAndRenderProducts();
});