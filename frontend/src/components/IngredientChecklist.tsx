import { useState, useEffect } from 'react';
import { Checkbox } from './ui/checkbox';
import { Label } from './ui/label';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

export interface IngredientItem {
  name: string;
  category: 'main' | 'side' | 'seasoning' | 'other';
  checked: boolean;
}

interface IngredientChecklistProps {
  ingredients: IngredientItem[];
  onChange: (selectedIngredients: string[]) => void;
  estimatedMatchRate?: number;
}

export function IngredientChecklist({ ingredients, onChange, estimatedMatchRate }: IngredientChecklistProps) {
  const [ingredientState, setIngredientState] = useState<IngredientItem[]>(ingredients);

  useEffect(() => {
    // ingredients prop이 변경되면 상태 업데이트 (참조 비교 문제 해결)
    setIngredientState([...ingredients]);
  }, [ingredients]);

  const handleToggle = (index: number) => {
    const updated = [...ingredientState];
    updated[index].checked = !updated[index].checked;
    setIngredientState(updated);
    
    const selected = updated.filter(ing => ing.checked).map(ing => ing.name);
    onChange(selected);
  };

  return (
    <div className="w-full space-y-6">
      {estimatedMatchRate !== undefined && (
        <Card className="bg-gradient-to-r from-orange-50 to-pink-50 border-orange-200">
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-1">예상 매칭률</p>
              <p className="text-3xl font-bold text-orange-600">{Math.round(estimatedMatchRate * 100)}%</p>
              <p className="text-xs text-gray-500 mt-1">일반 재료는 자동으로 체크 해제됨</p>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">필요한 재료</CardTitle>
          <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800 font-medium">
              ⚠️ 없는 재료를 체크하세요
            </p>
            <p className="text-xs text-blue-600 mt-1">
              체크한 재료는 집에 없는 재료로 인식되어 대체재료가 제안됩니다.
            </p>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {ingredientState.map((item, index) => (
              <div key={index} className="flex items-center space-x-2">
                <Checkbox
                  id={`ingredient-${index}`}
                  checked={item.checked}
                  onChange={() => handleToggle(index)}
                />
                <Label
                  htmlFor={`ingredient-${index}`}
                  className="text-sm font-normal cursor-pointer flex-1"
                >
                  {item.name}
                </Label>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
