import React, { useState } from 'react';
import { useItems, useItem } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle, Input, Button } from '@rpg/ui';
import type { Item } from '@rpg/types';

export function ItemBrowser() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const { data: items = [], loading } = useItems();
  const { data: selectedItem } = useItem(selectedItemId);

  const filteredItems = items.filter((item) =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="grid grid-cols-2 gap-4 h-full">
      <Card>
        <CardHeader>
          <CardTitle>Items</CardTitle>
          <Input
            placeholder="Search items..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="mt-2"
          />
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-muted-foreground text-sm">Loading...</p>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {filteredItems.length === 0 ? (
                <p className="text-muted-foreground text-sm">No items found</p>
              ) : (
                filteredItems.map((item) => (
                  <div
                    key={item.id}
                    className={`p-2 border rounded cursor-pointer hover:bg-accent ${
                      selectedItemId === item.id ? 'bg-accent' : ''
                    }`}
                    onClick={() => setSelectedItemId(item.id)}
                  >
                    <div className="font-semibold">{item.name}</div>
                    <div className="text-sm text-muted-foreground">
                      {item.type} • {item.rarity}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Item Details</CardTitle>
        </CardHeader>
        <CardContent>
          {selectedItem ? (
            <div className="space-y-4">
              <div>
                <h3 className="font-bold text-lg">{selectedItem.name}</h3>
                <p className="text-sm text-muted-foreground">
                  {selectedItem.type} • {selectedItem.rarity}
                </p>
              </div>
              <div>
                <p className="text-sm">{selectedItem.description}</p>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="font-semibold">Weight:</span> {selectedItem.weight} lbs
                </div>
                <div>
                  <span className="font-semibold">Price:</span> {selectedItem.price} cp
                </div>
              </div>
              {Object.keys(selectedItem.properties).length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Properties</h4>
                  <div className="text-sm space-y-1">
                    {Object.entries(selectedItem.properties).map(([key, value]) => (
                      <div key={key}>
                        <span className="font-semibold">{key}:</span> {String(value)}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">Select an item to view details</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

