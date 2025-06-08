// Replace the existing filterEquipment function with this:
function filterEquipment() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const categoryFilter = document.getElementById('categoryFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;
    
    const equipmentCards = document.querySelectorAll('.grid > div');
    
    equipmentCards.forEach(card => {
        const name = card.querySelector('h3').textContent.toLowerCase();
        const serialNumber = card.querySelector('p:nth-child(1)').textContent.toLowerCase();
        const category = card.querySelector('p:nth-child(2)').textContent.toLowerCase();
        const statusElement = card.querySelector('.rounded-full');
        const status = statusElement ? statusElement.textContent.trim().toLowerCase() : '';
        
        const matchesSearch = name.includes(searchTerm) || serialNumber.includes(searchTerm);
        const matchesCategory = !categoryFilter || category.includes(categoryFilter.toLowerCase());
        const matchesStatus = !statusFilter || status === statusFilter.toLowerCase();
        
        card.style.display = (matchesSearch && matchesCategory && matchesStatus) ? '' : 'none';
    });
}

// Add event listeners for filters
document.getElementById('searchInput').addEventListener('input', filterEquipment);
document.getElementById('categoryFilter').addEventListener('change', filterEquipment);
document.getElementById('statusFilter').addEventListener('change', filterEquipment);

// Remove the custom querySelector extension as it's not needed anymore