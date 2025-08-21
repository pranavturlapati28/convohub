'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/simple-tabs'

export default function TestPage() {
  return (
    <div className="min-h-screen bg-background p-8">
      <h1 className="text-2xl font-bold mb-4">Component Test Page</h1>
      
      <div className="space-y-8">
        {/* Button Test */}
        <div>
          <h2 className="text-lg font-semibold mb-2">Button Component</h2>
          <div className="space-x-2">
            <Button>Default Button</Button>
            <Button variant="outline">Outline Button</Button>
            <Button variant="secondary">Secondary Button</Button>
            <Button variant="destructive">Destructive Button</Button>
          </div>
        </div>

        {/* Tabs Test */}
        <div>
          <h2 className="text-lg font-semibold mb-2">Tabs Component</h2>
          <Tabs defaultValue="tab1">
            <TabsList>
              <TabsTrigger value="tab1">Tab 1</TabsTrigger>
              <TabsTrigger value="tab2">Tab 2</TabsTrigger>
              <TabsTrigger value="tab3">Tab 3</TabsTrigger>
            </TabsList>
            <TabsContent value="tab1" className="p-4 border rounded">
              <p>Content for Tab 1</p>
            </TabsContent>
            <TabsContent value="tab2" className="p-4 border rounded">
              <p>Content for Tab 2</p>
            </TabsContent>
            <TabsContent value="tab3" className="p-4 border rounded">
              <p>Content for Tab 3</p>
            </TabsContent>
          </Tabs>
        </div>

        {/* Success Message */}
        <div className="p-4 bg-green-100 border border-green-400 text-green-700 rounded">
          <h3 className="font-semibold">✅ All Components Working!</h3>
          <p>If you can see this page, all the basic components are functioning correctly.</p>
        </div>
      </div>
    </div>
  )
}
